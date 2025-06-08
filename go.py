import sys, sysconfig

print("python version:", sys.version)

status = sysconfig.get_config_var("Py_GIL_DISABLED")

print("GIL status:", status)