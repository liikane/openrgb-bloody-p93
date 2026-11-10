#pragma once
#include <atomic>
#include <vector>
#include <QObject>
#include <QWidget>
#include <QCheckBox>
#include <QLabel>
#include <QPushButton>
#include <QSpinBox>
#include <QLineEdit>
#include <QTimer>
#include <QUdpSocket>
#include "OpenRGBPluginInterface.h"
#include "P93Hid.h"

class BloodyP93Plugin final : public QObject, public OpenRGBPluginInterface
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID OpenRGBPluginInterface_IID FILE "plugin.json")
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
    void TickBeacon();
    bool ParseGroups(std::vector<std::size_t>& left, std::vector<std::size_t>& right);
    void HandleNotification();

    OpenRGBPluginAPIInterface* api_ = nullptr;
    RGBControllerInterface* controller_ = nullptr;
    P93Hid device_;
    QWidget* widget_ = nullptr;
    QCheckBox* enable_ = nullptr;
    QLabel* status_ = nullptr;
    QLabel* slot_status_ = nullptr;
    QCheckBox* beacon_ = nullptr;
    QSpinBox* interval_ = nullptr;
    QLineEdit* left_slots_ = nullptr;
    QLineEdit* right_slots_ = nullptr;
    QTimer* beacon_timer_ = nullptr;
    QTimer* notification_timeout_ = nullptr;
    QCheckBox* notifications_ = nullptr;
    QUdpSocket* notification_socket_ = nullptr;
    P93Protocol::Color beacon_color_ = {255, 210, 0};
    bool beacon_phase_ = false;
    int next_slot_ = 0;
    std::atomic<bool> enabled_{false};
};
