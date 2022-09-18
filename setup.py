import datetime
import arcpy

script_path = "C:\\Users\\wiema\\PycharmProjects\\Forschungsprojekt\\"
project_path = "C:\\Users\\wiema\\PycharmProjects\\Forschungsprojekt\\arcgisproject\\"
project_name = "arcgisproject.aprx"
database_path = "C:\\Users\\wiema\\PycharmProjects\\Forschungsprojekt\\arcgisproject\\"
database_name = "Forschungsprojekt.gdb"
database_file = database_path + database_name
database_file_path = database_file + "\\"


def log(message):
    now = datetime.datetime.now()
    print(now.strftime("%H:%M:%S") + " | " + message)


def init_arcpy():
    log("Initializing ArcGIS")
    arcpy.mp.ArcGISProject(project_path + project_name)
    arcpy.env.workspace = database_file
    arcpy.env.parallelProcessingFactor = 8
    arcpy.env.overwriteOutput = True


def get_data_base_path(file_name):
    return database_file_path + file_name


def get_local_file_path(file_name):
    return script_path + file_name


def clear_database():
    log("Deleting database.")
    arcpy.management.Delete(database_file)
    log("Creating database.")
    arcpy.CreateFileGDB_management(database_path, database_name)


def import_geojson(file_name, feature_name, feature_geometry_type):
    log("Importing " + file_name + " as " + feature_name)
    log(get_data_base_path(feature_name))
    arcpy.conversion.JSONToFeatures(get_local_file_path(file_name), get_data_base_path(feature_name),
                                    feature_geometry_type)

