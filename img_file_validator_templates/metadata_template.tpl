{
    "NOTE_INFO":"Attribues with _INFO only contain desriptions to outline fields / can be deleted. The most important stuff to be supplied is at the beginning of this file. Also check the file settings template that contains more information. Only Fields containing _TODO_ requires individual setup to your situation, rest can be left as it is. Check the template Files in Github Repo in subfolder .../img_file_validator_templates/...",
    
    "EXIFTOOL_FILE_INFO":"Path to Exiftool executable",
    "EXIFTOOL_FILE": "C:/<path to _TODO_ >/exiftool.exe",

    "META_PROFILES_FILE_INFO":"JSON File to define EXIF Keyword Profiles to comfortably select sets for a given image folder",    
    "META_PROFILES_FILE": "_TODO_ C:/<P_CONTROL Path>/metadata_exif_keywords_template.json",    
    
    "KEYWORD_HIER_FILE_INFO":"File location of hierarchical keywords. The Hierarchical Keywords metadata will be accordingly supplied if it finds a used keyword that is also a leaf / node without childrens",       
    "KEYWORD_HIER_FILE": "_TODO_ C:/<P_CONTROL Path>/metadata_hierarchy.txt",        
    
    "DEFAULT_LATLON_INFO":" _TODO_ Use this as default lat lon fallback when neither GPS Tracks nor open street map links are available. Will also be rewritten to location of OSM link or calibration location of gps track",   
    "DEFAULT_LATLON": [52.5143,13.3502],      
      
    "CALIB_OFFSET_INFO": "_TODO_ OFFSET as integer in seconds: T(GPS)=T(CAMERA)+T(OFFSET). if parameter CALIB_OFFSET is supplied, it will be used instead of CALIB_DATETIME / Rename this to CALIB_OFFSET in case you have it upfront / set it to 0, then no offset calculation between GPS and Image DateTime will be applied",    
    "XCALIB_OFFSET": 600,    
    
    "CALIB_DATETIME_INFO": "_TODO_ DATE TIME OF GPS LOGGER WHEN IMAGE WAS TAKEN (extracted from GPS WAYPOINT OR MANUALLY ENTERED HERE)",
    "CALIB_DATETIME": "2022:10:08 17:22:47",
    
    "TIMEZONE_INFO":"_TODO_ Use Timezone. Use Timezones as defined by pytz Python module. Note that for newest IPTC standards timezone also should be available in image metadata but can't be taken for granted (which is the case for some Panorama cameras)",        
    "TIMEZONE": "Europe/Berlin",      
    
    "COPYRIGHT_INFO":"Supply your Copyright information",   
    "COPYRIGHT": "_TODO_ <YOUR_NAME>",
    "COPYRIGHT_NOTICE": "(C) 2022 _TODO_ <YOUR_NAME>",
    "INFO_CREDIT": "_TODO_ <YOUR_NAME>",
    "CREDIT": "_TODO_ <YOUR_NAME>",
    "SOURCE": "Own Photography",       
    
    "CALIB_IMG_FILE_INFO": "Image showing GPS logger with date to be used to extract DateTime",
    "CALIB_IMG_FILE": "gps.jpg",      

    "META_FILE_INFO":"Name of EXIF keywords file. Based on META_PROFILES_FILE you can create this file when using the validator file",       
    "META_FILE": "metadata_exif.tpl",    

    "GPX_FILE_INFO":"Name of GPS log (to be placed in image folder)",       
    "GPX_FILE": "gps.gpx",    

    "WAYPOINT_FILE_INFO":"Name of GPS waypoint file (to be placed in image folder)",       
    "WAYPOINT_FILE": "gps_wpt.gpx",        
    
    "DEFAULT_LATLON_FILE_INFO":"Name of file containing reverse GPS geolocation data",       
    "DEFAULT_LATLON_FILE": "default.geo",
    
    "WORK_DIR_INFO":"Fixed Working Directory, left blank",       
    "WORK_DIR": "",
    
    "IMG_EXTENSIONS_INFO":"Filetypes for which metadata will be inserted",       
    "IMG_EXTENSIONS": [
        "jpg"
    ],
    
    "TECH_KEYWORDS_INFO":"Flag: Add some technical keywords from Maker Notes to IPTC keywords",       
    "TECH_KEYWORDS": true,
    
    "OVERWRITE_KEYWORD_INFO":"",   
    "OVERWRITE_KEYWORD": true,
    
    "OVERWRITE_META_INFO":"Overwrite any EXIF metadata when triggering metadata changes / adding should also work but never really tried",         
    "OVERWRITE_META": true,

    "CREATE_GEO_METADATA_INFO":"Create Control Files that contain data from reverse Geo Lookup",    
    "CREATE_GEO_METADATA": true,   
    
    "CREATE_LATLON_INFO":"Flag: Create LatLon Info files",    
    "CREATE_LATLON": "C",
    
    "CREATE_DEFAULT_LATLON_INFO":"Flag: Create Default LatLon file, named [DEFAULT_LATLON_FILE]",    
    "CREATE_DEFAULT_LATLON": "C",
 
    "DEFAULT_MAP_DETAIL_INFO":"Zoom level for OSM Links to be created",  
    "DEFAULT_MAP_DETAIL": 18,
    
    "DEFAULT_GPS_EXT_INFO":"File Type extension for files containing reverse geo information",     
    "DEFAULT_GPS_EXT": "geo",
  
    "GPS_READ_REMOTE_INFO": "Execute Reverse Geo Location Search on nominatim openstreetmap. Reverse Geolocation Search will be throttled / only limited capability available",
    "GPS_READ_REMOTE": true
}