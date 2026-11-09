#pragma once
#include <atomic>
#include <QObject>
#include <QWidget>
#include <QCheckBox>
#include <QLabel>
#include <QPushButton>
#include "OpenRGBPluginInterface.h"
#include "P93Hid.h"

class BloodyP93Plugin final : public QObject, public OpenRGBPluginInterface
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID OpenRGBPluginInterface_IID)
    Q_INTERFACES(OpenRGBPluginInterface)

public:
    OpenRGBPluginInfo GetPluginInfo() override;
    unsigned int GetPluginAPIVersion() override;
    void Load(OpenRGBPluginAPIInterface* api) override;
    QWidget* GetWidget() override;
    QMenu* GetTrayMenu() override;
    void Unload() override;
    void OnProfileAboutToLoad() override;
    void OnProfileLoad(nlohmann::json data) override;
    nlohmann::json OnProfileSave() override;
    unsigned char* OnSDKCommand(unsigned int pkt_id, unsigned char* pkt_data, unsigned int* pkt_size) override;
    void ProfileManagerUpdated(unsigned int reason) override;
    void ResourceManagerUpdated(unsigned int reason) override;
    void SettingsManagerUpdated(unsigned int reason) override;

private:
    static void DeviceUpdateLEDs(void* self);
    static void DeviceUpdateZoneLEDs(void* self, int zone);
    static void DeviceUpdateSingleLED(void* self, int led);
    void RegisterDevice();
    void ApplyColor();

    OpenRGBPluginAPIInterface* api_ = nullptr;
    RGBControllerInterface* controller_ = nullptr;
    P93Hid device_;
    QWidget* widget_ = nullptr;
    QCheckBox* enable_ = nullptr;
    QLabel* status_ = nullptr;
    std::atomic<bool> enabled_{false};
};
