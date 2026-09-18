
from database import get_db_connection
from datetime import date, timedelta
import requests
import pyfao56

# have to check the status code before using the JSON files blindly - Valavan
def fetch_weather_api(lat, lon, target_date):
    """Wrapper for NASA POWER API."""
    date_str = target_date.strftime("%Y%m%d")
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX,T2M_MIN,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR&community=ag&longitude={lon}&latitude={lat}&start={date_str}&end={date_str}&format=JSON"
    try:
        response = requests.get(url, timeout=10).json()
        return {
            "temp_max": response['properties']['parameter']['T2M_MAX'][date_str],
            "temp_min": response['properties']['parameter']['T2M_MIN'][date_str],
            "rh": response['properties']['parameter']['RH2M'][date_str],
            "wind_speed": response['properties']['parameter']['WS2M'][date_str],
            "solar_rad": response['properties']['parameter']['ALLSKY_SFC_SW_DWN'][date_str],
            "precip": response['properties']['parameter']['PRECTOTCORR'][date_str]
        }
    except Exception:
        # Fallback values if API fails - check this -Valavan
        return {"temp_max": 30.0, "temp_min": 22.0, "rh": 75.0, "wind_speed": 2.5, "solar_rad": 15.0, "precip": 0.0}

def fetch_spatial_api(lat, lon):
    """Wrapper for ISRIC SoilGrids REST API."""
    # This endpoint specifically requests sand and clay data for the 0-5cm depth layer
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}&property=sand&property=clay&depth=0-5cm&value=mean"
    
    try:
        response = requests.get(url, timeout=10).json()
        
        # Setting our fallbacks just in case the extraction fails - check these values-Valavan
        sand_val = 45.0
        clay_val = 25.0
        
        # SoilGrids nests its data inside 'properties' -> 'layers'
        for layer in response.get('properties', {}).get('layers', []):
            name = layer.get('name')
            # SoilGrids returns these values in grams per kilogram. Dividing by 10 gives us the percentage.
            mean_value = layer.get('depths', [{}])[0].get('values', {}).get('mean', 0) / 10.0
            
            if name == 'sand':
                sand_val = mean_value
            elif name == 'clay':
                clay_val = mean_value
                
        return {"sand_pct": sand_val, "clay_pct": clay_val}
        
    except Exception as e:
        print(f"[API ERROR] SoilGrids extraction failed: {e}")
        # Return fallback values so the pipeline doesn't crash
        return {"sand_pct": 45.0, "clay_pct": 25.0}

# there are two functions called elevation need to find the suitbable one.-Valavan
def fetch_elevation_api(lat, lon):
    """Wrapper for Google Maps Elevation API."""
    # check for expiry- Valavan
    ELEVATION_API_KEY = "b7ffa9a639148b1975d19bc41f0b9eab" 
    
    url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lon}&key={ELEVATION_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10).json() 
        
        # Google returns a "status" field we should check
        if response.get('status') == 'OK':
            return float(response['results'][0]['elevation'])
        else:
            print(f"[API ERROR] Google Elevation failed with status: {response.get('status')}")
            return 10.0  # Fallback elevation
            
    except Exception as e:
        print(f"[API ERROR] Network failure when fetching elevation: {e}")
        return 10.0  # Fallback elevation

def fetch_elevation_api(lat, lon):
    """Wrapper for OpenTopoData API (Free DEM alternative)."""
    url = f"https://api.opentopodata.org/v1/srtm90m?locations={lat},{lon}"
    try:
        response = requests.get(url, timeout=10).json()
        return float(response['results'][0]['elevation'])
    except Exception:
        # Fallback elevation if API fails
        return 10.0

def calculate_kc(dap, c_data):
    """Piecewise FAO-56 Crop Coefficient Calculation."""
    l1 = c_data['L_ini']
    l2 = l1 + c_data['L_dev']
    l3 = l2 + c_data['L_mid']
    l4 = l3 + c_data['L_late']

    if dap <= l1:
        return float(c_data['kc_ini'])
    elif dap <= l2:
        return float(c_data['kc_ini'] + ((dap - l1) / c_data['L_dev']) * (c_data['kc_mid'] - c_data['kc_ini']))
    elif dap <= l3:
        return float(c_data['kc_mid'])
    elif dap <= l4:
        return float(c_data['kc_mid'] + ((dap - l3) / c_data['L_late']) * (c_data['kc_end'] - c_data['kc_mid']))
    return float(c_data['kc_end'])

def calculate_and_store_features(plot_id: int, cycle_id: int, target_date: date):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # 1. Fetch Plot & Crop Data
    cursor.execute("SELECT latitude, longitude, elevation FROM plot WHERE plot_id = %s", (plot_id,))
    plot_data = cursor.fetchone()
    lat = float(plot_data['latitude'])
    lon = float(plot_data['longitude'])
    
    cursor.execute("""
        SELECT c.*, pr.planting_date, sp.field_capacity, sp.wilting_point, sp.taw 
        FROM planting_record pr 
        JOIN crop c ON pr.crop_id = c.crop_id 
        JOIN soil_profile sp ON sp.plot_id = pr.plot_id
        WHERE pr.cycle_id = %s
    """, (cycle_id,))
    crop_data = cursor.fetchone()

    # 2. API Calls for Weather, Spatial, and Elevation
    weather = fetch_weather_api(lat, lon, target_date)
    dynamic_elevation = fetch_elevation_api(lat, lon)
    
    # Save Weather to DB
    cursor.execute("""
        INSERT IGNORE INTO weather_daily 
        (plot_id, recorded_date, temp_max, temp_min, relative_humidity, wind_speed, solar_rad, precipitation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (plot_id, target_date, weather['temp_max'], weather['temp_min'], weather['rh'], 
          weather['wind_speed'], weather['solar_rad'], weather['precip']))

    # Optionally update the plot table with the newly fetched exact elevation
    cursor.execute("UPDATE plot SET elevation = %s WHERE plot_id = %s", (dynamic_elevation, plot_id))

    # 3. Calculate DAP & Kc
    dap = (target_date - crop_data['planting_date']).days
    kc = calculate_kc(dap, crop_data)

    # 4. Calculate ETo using pyfao56
    doy = target_date.timetuple().tm_yday
    rad = pyfao56.parameters.Rad(lat, dynamic_elevation)
    eto = pyfao56.refet.eto_pm(
        tmin=weather['temp_min'], tmax=weather['temp_max'],
        ea=pyfao56.refet.ea_obs(weather['temp_min'], weather['temp_max'], weather['rh']),
        uz=weather['wind_speed'], rs=weather['solar_rad'], 
        ra=rad.ra(doy), 
        lat=lat,
        z=dynamic_elevation
    )

    # 5. Fetch trailing data (3-day and 7-day)
    cursor.execute("""
        SELECT SUM(precipitation) as rain_3d, AVG(eto) as eto_3d 
        FROM (SELECT precipitation FROM weather_daily WHERE plot_id=%s ORDER BY recorded_date DESC LIMIT 3) w,
             (SELECT eto FROM daily_analytics WHERE plot_id=%s ORDER BY recorded_date DESC LIMIT 3) e
    """, (plot_id, plot_id))
    trailing = cursor.fetchone()
    rain_3d = trailing.get('rain_3d') or 0
    eto_3d = trailing.get('eto_3d') or eto

    cursor.execute("SELECT SUM(precipitation) as rain_7d FROM weather_daily WHERE plot_id=%s ORDER BY recorded_date DESC LIMIT 7", (plot_id,))
    rain_7d = cursor.fetchone().get('rain_7d') or 0

    # 6. Fetch Sensor Data for Depletion & Trend
    cursor.execute("SELECT soil_moisture_vwc FROM sensor_reading WHERE DATE(recorded_at) = %s ORDER BY recorded_at DESC LIMIT 1", (target_date,))
    current_moisture_row = cursor.fetchone()
    current_vwc = float(current_moisture_row['soil_moisture_vwc']) / 100 if current_moisture_row else float(crop_data['field_capacity'])

    cursor.execute("SELECT soil_moisture_vwc FROM sensor_reading WHERE DATE(recorded_at) = %s", (target_date - timedelta(days=3),))
    old_moisture_row = cursor.fetchone()
    moisture_trend_3d = (current_vwc - (float(old_moisture_row['soil_moisture_vwc'])/100)) / 3 if old_moisture_row else 0.0

    # 7. Depletion Calculations
    dr_measured = (float(crop_data['field_capacity']) - current_vwc) * float(crop_data['root_depth_zr']) * 1000
    depletion_ratio_measured = max(0.0, dr_measured / float(crop_data['taw']))

    # FAO-56 Bucket Model (Simulated)
    cursor.execute("SELECT depletion_ratio_simulated FROM daily_analytics WHERE plot_id=%s ORDER BY recorded_date DESC LIMIT 1", (plot_id,))
    last_sim = cursor.fetchone()
    last_dr = (float(last_sim['depletion_ratio_simulated']) * float(crop_data['taw'])) if last_sim else 0.0
    
    etc = kc * eto
    dr_simulated = max(0.0, min(float(crop_data['taw']), last_dr - weather['precip'] + etc))
    depletion_ratio_simulated = dr_simulated / float(crop_data['taw'])
    
    sim_vs_measured_deviation = depletion_ratio_measured - depletion_ratio_simulated

    # 8. Save to Database
    insert_query = """
    INSERT INTO daily_analytics 
    (plot_id, cycle_id, recorded_date, eto, rain_3d_sum, rain_7d_sum, eto_3d_mean, dap, kc, 
    moisture_trend_3d, depletion_ratio_measured, depletion_ratio_simulated, sim_vs_measured_deviation)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        plot_id, cycle_id, target_date, eto, rain_3d, rain_7d, eto_3d, dap, kc, 
        moisture_trend_3d, depletion_ratio_measured, depletion_ratio_simulated, sim_vs_measured_deviation
    ))

    db.commit()
    cursor.close()
    db.close()
    print(f"[FEATURE ENG] Computed and stored all API/Physics features (including dynamic elevation) for {target_date}")
