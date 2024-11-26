MODEL_VALUE = "Model"
MAKE_VALUE = "Make"
LENS_VALUE = "LensModel"
PARAM_VALUE = "Param"
DATETIME_VALUE = "Datetime"
DATE_VALUE = "Date"
CUSTOM_VALUE = "Custom"
NONE_VALUE = "None"
LENS_MAKE_LENS_MODEL_VALUE = "LensMake_LensModel"
CAMERA_MODEL_LENS_MODEL_VALUE = "CameraModel_LensModel"
TOTAL_PIXEL_VALUE = "TotalPixel"
CAMERA_MAKE_CAMERA_MODEL_VALUE = "CameraMake_CameraModel"
FILENAME_VALUE = "Filename"
DATE_FILENAME_VALUE = "Date_Filename"
DATETIME_FILENAME_VALUE = "Datetime_Filename"
GEO_INFO_VALUE = "GeoInfo"

MODELS = {
    MODEL_VALUE: "相机型号(eg. Nikon Z7)",
    MAKE_VALUE: "相机厂商(eg. Nikon)",
    LENS_VALUE: "镜头型号(eg. Nikkor 24-70 f/2.8)",
    PARAM_VALUE: "拍摄参数(eg. 50mm f/1.8 1/1000s ISO 100)",
    DATETIME_VALUE: "拍摄时间(eg. 2023-01-01 12:00)",
    DATE_VALUE: "拍摄日期(eg. 2023-01-01)",
    CUSTOM_VALUE: "自定义",
    NONE_VALUE: "(无)",
    LENS_MAKE_LENS_MODEL_VALUE: "镜头厂商 + 镜头型号(eg. Nikon Nikkor 24-70 f/2.8)",
    CAMERA_MODEL_LENS_MODEL_VALUE: "相机型号 + 镜头型号(eg. Nikon Z7 Nikkor 24-70 f/2.8)",
    TOTAL_PIXEL_VALUE: "总像素(MP)",
    CAMERA_MAKE_CAMERA_MODEL_VALUE: "相机厂商 + 相机型号(eg. DJI FC123)",
    FILENAME_VALUE: "文件名",
    DATE_FILENAME_VALUE: "日期 + 文件名(eg. 2023-01-01 DXO_0001)",
    DATETIME_FILENAME_VALUE: "日期时间 + 文件名(eg. 2023-01-01 12:00 DXO_0001)",
    GEO_INFO_VALUE: "地理信息",
}

LOCATION_LEFT_TOP = "left_top"
LOCATION_LEFT_BOTTOM = "left_bottom"
LOCATION_RIGHT_TOP = "right_top"
LOCATION_RIGHT_BOTTOM = "right_bottom"
TRANSPARENT = (0, 0, 0, 0)
DEBUG = False
GRAY = "#CBCBC9"

DEFAULT_VALUE = "--"
TINY_HEIGHT = 800

COLOR_SCHEME_NAMES = {
    "default": "默认",
    "reverse": "反色",
    "blackred": "黑红",
    "custom": "自定义",
}
