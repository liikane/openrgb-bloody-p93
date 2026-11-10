TEMPLATE = lib
CONFIG += plugin c++17
QT += core gui widgets network
TARGET = OpenRGBBloodyP93Plugin

OPENRGB_SOURCE_DIR = $$(OPENRGB_SOURCE_DIR)
isEmpty(OPENRGB_SOURCE_DIR): error("Set OPENRGB_SOURCE_DIR to a matching OpenRGB 1.1 source directory")

INCLUDEPATH += $$OPENRGB_SOURCE_DIR
INCLUDEPATH += $$OPENRGB_SOURCE_DIR/RGBController
INCLUDEPATH += $$OPENRGB_SOURCE_DIR/dependencies
INCLUDEPATH += $$OPENRGB_SOURCE_DIR/dependencies/include
INCLUDEPATH += $$OPENRGB_SOURCE_DIR/dependencies/json

HEADERS += src/BloodyP93Plugin.h src/P93Hid.h src/P93Protocol.h
SOURCES += src/BloodyP93Plugin.cpp src/P93Hid.cpp

win32:LIBS += -lsetupapi -lhid
DESTDIR = $$PWD/dist
