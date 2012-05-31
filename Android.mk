robotframework_LOCAL_PATH := $(call my-dir)

ifndef python_install_marker
include $(robotframework_LOCAL_PATH)/../python-for-android/python-build/build/build.mk
endif

LOCAL_PATH := $(robotframework_LOCAL_PATH)

include $(CLEAR_VARS)

LOCAL_MODULE_SUBDIR := python2.6/

LOCAL_MODULE_TAGS    := optional
LOCAL_MODULE         := robotframework

LOCAL_MODULE_CLASS := INTERMEDIATES
LOCAL_UNINSTALLABLE_MODULE := true

LOCAL_PRELINK_MODULE := false

include $(BUILD_SYSTEM)/base_rules.mk

robotframework_intermediates := $(shell pwd)/$(intermediates)

robotframework_marker := \
   $(robotframework_intermediates)/lib/python2.6/site-packages/robot/run.pyc

robotframework_install_marker := \
   $(TARGET_OUT_SHARED_LIBRARIES)/python2.6/site-packages/robot/run.pyc

$(LOCAL_BUILT_MODULE): $(robotframework_install_marker)

# TODO: The following rule is currently an ugly hack.  Fix.
$(robotframework_install_marker): $(robotframework_marker)
	@echo "Install: $@"
	$(hide) mkdir -p $(dir $@)
	$(hide) $(ACP) -fptr $(dir $<)/* $(dir $@)

$(robotframework_marker): $(python_install_marker)
	$(hide) (cd $(LOCAL_PATH); \
	    $(host_python_install_dir)/bin/python setup.py install \
	        --build-base=$(robotframework_intermediates)/build \
		--prefix=$(robotframework_intermediates))

LOCAL_MODULE_SUBDIR :=
