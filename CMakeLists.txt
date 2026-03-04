cmake_minimum_required(VERSION 3.16)

project(ControleCorteDobra VERSION 0.1 LANGUAGES CXX)

# Ensure CMake can find the Qt6 installation – overrideable by user.
if(NOT DEFINED Qt6_DIR)
    # hard-coded to the known installed Qt version on this machine
    set(Qt6_DIR "C:/Qt/6.10.2/mingw_64/lib/cmake/Qt6" CACHE PATH "Qt6 CMake directory")
endif()

# Add Qt to prefix path in case some modules look there directly
list(APPEND CMAKE_PREFIX_PATH "${Qt6_DIR}")

set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Locate Qt6 (or fallback to Qt5 if needed).
# The original generic "QT" package caused a version compatibility error when
# CMake found Qt 6.10.2.  Requesting the specific Qt6 package directly avoids
# the empty-version check and makes the configuration reliable.
#
# The explicit version in the find_package call caused CMake to report
# incompatibility due to the "(64bit)" suffix in Qt6Config.cmake.
# Instead rely on the prefix path and allow any Qt6 6.x installation.
#
# Qt6Config may append "(64bit)" to the version string which breaks
# CMake's standard version comparison logic.  We can simply disable the
# check so that any Qt6 installation is accepted.
set(QT_NO_PACKAGE_VERSION_CHECK TRUE CACHE BOOL "Disable Qt version compatibility check")

# Ensure the version variable isn't empty; Qt's config file treats an
# empty requested version as incompatible.  We only need a minimum bound.
# keep this in cache so find_package sees it
set(Qt6_FIND_VERSION "6.0" CACHE STRING "Minimum Qt6 version to locate" FORCE)

find_package(Qt6 REQUIRED COMPONENTS Widgets LinguistTools)
# equivalent for Qt5 would be:
# find_package(Qt5 COMPONENTS Widgets LinguistTools)

set(TS_FILES ControleCorteDobra_pt_BR.ts)

set(PROJECT_SOURCES
        main.cpp
        mainwindow.cpp
        mainwindow.h
        mainwindow.ui
        ${TS_FILES}
)

# We only support Qt6 in this project so configure the executable directly.
qt_add_executable(ControleCorteDobra
    MANUAL_FINALIZATION
    ${PROJECT_SOURCES}
)

# Define target properties for Android with Qt 6 as:
#    set_property(TARGET ControleCorteDobra APPEND PROPERTY QT_ANDROID_PACKAGE_SOURCE_DIR
#                 ${CMAKE_CURRENT_SOURCE_DIR}/android)
# For more information, see https://doc.qt.io/qt-6/qt-add-executable.html#target-creation

qt_create_translation(QM_FILES ${CMAKE_SOURCE_DIR} ${TS_FILES})

target_link_libraries(ControleCorteDobra PRIVATE Qt${QT_VERSION_MAJOR}::Widgets)

# Qt for iOS sets MACOSX_BUNDLE_GUI_IDENTIFIER automatically since Qt 6.1.
# If you are developing for iOS or macOS you should consider setting an
# explicit, fixed bundle identifier manually though.
if(${QT_VERSION} VERSION_LESS 6.1.0)
  set(BUNDLE_ID_OPTION MACOSX_BUNDLE_GUI_IDENTIFIER com.example.ControleCorteDobra)
endif()
set_target_properties(ControleCorteDobra PROPERTIES
    ${BUNDLE_ID_OPTION}
    MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
    MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}
    MACOSX_BUNDLE TRUE
    WIN32_EXECUTABLE TRUE
)

include(GNUInstallDirs)
install(TARGETS ControleCorteDobra
    BUNDLE DESTINATION .
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

if(QT_VERSION_MAJOR EQUAL 6)
    qt_finalize_executable(ControleCorteDobra)
endif()
