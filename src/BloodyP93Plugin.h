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
#include <cstdint>
#include <QByteArray>
#include <QColor>
#include <QStringList>
#include "OpenRGBPluginInterface.h"
#include "P93Hid.h"
#include "P93Signals.h"

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
    void TickIdle();
    void StartIdle();
    void AddNotification(P93Signals::Event kind);
    void AcknowledgeAll();
    void UpdatePendingLabel();
    void UpdateColorButtons();
    bool ParseGroups(std::vector<std::size_t>& left, std::vector<std::size_t>& right);
    void HandleNotification();
    bool StartNotificationListener();
    void StopNotificationListener();

    OpenRGBPluginAPIInterface* api_ = nullptr;
    RGBControllerInterface* controller_ = nullptr;
    P93Hid device_;
    QWidget* widget_ = nullptr;
    QCheckBox* enable_ = nullptr;
    QLabel* status_ = nullptr;
    QLabel* slot_status_ = nullptr;
    QCheckBox* beacon_ = nullptr;
    QSpinBox* interval_ = nullptr;
    QPushButton* beacon_color_a_button_ = nullptr;
    QPushButton* beacon_color_b_button_ = nullptr;
    QLineEdit* left_slots_ = nullptr;
    QLineEdit* right_slots_ = nullptr;
    QTimer* beacon_timer_ = nullptr;
    QTimer* idle_timer_ = nullptr;
    QCheckBox* idle_enabled_ = nullptr;
    QSpinBox* idle_interval_ = nullptr;
    QLabel* pending_label_ = nullptr;
    QPushButton* acknowledge_button_ = nullptr;
    QCheckBox* notifications_ = nullptr;
    QTimer* notification_poller_ = nullptr;
    QTimer* color_persistence_timer_ = nullptr;
    QStringList pending_colors_;
    std::uintptr_t notification_socket_handle_ = ~std::uintptr_t{0};
    QColor beacon_color_a_{255, 210, 0};
    QColor beacon_color_b_{255, 210, 0};
    std::vector<P93Signals::Event> pending_events_;
    std::size_t notification_tick_ = 0;
    std::size_t idle_step_ = 0;
    bool beacon_phase_ = false;
    int next_slot_ = 0;
    std::atomic<bool> enabled_{false};
};
