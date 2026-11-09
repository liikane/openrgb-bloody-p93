#include "BloodyP93Plugin.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFont>
#include <QPushButton>
#include <QCheckBox>

OpenRGBPluginInfo BloodyP93Plugin::GetPluginInfo()
{
    OpenRGBPluginInfo info{};
    info.Name = "Bloody P93 RGB Bridge";
    info.Description = "Experimental Windows HID RGB support for Bloody P93 (09DA:31DE)";
    info.Version = "0.1.0";
    info.Commit = "community-preview";
    info.URL = "https://github.com/liikane/openrgb-bloody-p93";
    info.Location = OPENRGB_PLUGIN_LOCATION_SETTINGS;
    info.Label = "Bloody P93";
    info.ProtocolVersion = 0;
    return info;
}

unsigned int BloodyP93Plugin::GetPluginAPIVersion()
{
    return OPENRGB_PLUGIN_API_VERSION;
}

void BloodyP93Plugin::Load(OpenRGBPluginAPIInterface* api)
{
    api_ = api;
    widget_ = new QWidget();
    auto* layout = new QVBoxLayout(widget_);
    auto* title = new QLabel("Bloody P93 RGB Bridge", widget_);
    QFont font = title->font();
    font.setBold(true);
    title->setFont(font);
    layout->addWidget(title);

    status_ = new QLabel("Checking Bloody P93 HID device...", widget_);
    status_->setWordWrap(true);
    layout->addWidget(status_);

    enable_ = new QCheckBox("Enable RGB control (experimental)", widget_);
    enable_->setEnabled(false);
    layout->addWidget(enable_);

    auto* retry = new QPushButton("Retry device detection", widget_);
    layout->addWidget(retry);

    auto* instructions = new QLabel(
        "Windows only. Changes RGB colors via verified 64-byte HID Feature reports. "
        "Does not rewrite buttons, macros, firmware or profiles. "
        "No writes are sent until you tick Enable.", widget_);
    instructions->setWordWrap(true);
    layout->addWidget(instructions);
    layout->addStretch(1);

    connect(enable_, &QCheckBox::toggled, this, [this](bool value) {
        enabled_.store(value);
        if(value)
        {
            ApplyColor();
        }
    });

    connect(retry, &QPushButton::clicked, this, [this] {
        if(controller_ != nullptr)
        {
            return;
        }
        RegisterDevice();
    });

    RegisterDevice();
}

void BloodyP93Plugin::RegisterDevice()
{
    if(api_ == nullptr || controller_ != nullptr)
    {
        return;
    }

    std::string error;
    if(!device_.Connect(error))
    {
        status_->setText(QString::fromStdString(error));
        enable_->setEnabled(false);
        return;
    }

    RGBController_Setup setup{};
    setup.description = "Community HID controller. Experimental support, no firmware writes.";
    setup.location = "HID 09DA:31DE MI_02 COL04";
    setup.name = "Bloody P93 (community)";
    setup.vendor = "Bloody";
    setup.version = "0.1.0";
    setup.active_mode = 0;
    setup.type = DEVICE_TYPE_MOUSE;
    setup.flags = CONTROLLER_FLAG_VIRTUAL;

    mode direct{};
    direct.name = "Direct";
    direct.value = 1;
    direct.flags = MODE_FLAG_HAS_PER_LED_COLOR;
    direct.color_mode = MODE_COLORS_PER_LED;
    setup.modes.push_back(direct);

    zone all{};
    all.name = "All RGB lights";
    all.type = ZONE_TYPE_SINGLE;
    all.start_idx = 0;
    all.leds_count = 1;
    all.leds_min = 1;
    all.leds_max = 1;
    setup.zones.push_back(all);

    led combined{};
    combined.name = "Mouse RGB";
    combined.value = 0;
    setup.leds.push_back(combined);

    setup.object_ptr = this;
    setup.DeviceUpdateLEDs = &BloodyP93Plugin::DeviceUpdateLEDs;
    setup.DeviceUpdateZoneLEDs = &BloodyP93Plugin::DeviceUpdateZoneLEDs;
    setup.DeviceUpdateSingleLED = &BloodyP93Plugin::DeviceUpdateSingleLED;

    controller_ = api_->CreateVirtualRGBController(&setup);
    if(controller_ == nullptr)
    {
        status_->setText("Failed to create OpenRGB virtual controller");
        device_.Close();
        return;
    }

    // A known color until user opts into hardware writes.
    controller_->SetColor(0, ToRGBColor(160, 0, 255));
    api_->RegisterVirtualRGBController(controller_);
    status_->setText("Bloody P93 connected. RGB writes are disabled until you enable them.");
    enable_->setEnabled(true);
}

void BloodyP93Plugin::ApplyColor()
{
    if(!enabled_.load() || controller_ == nullptr)
    {
        return;
    }

    RGBColor c = controller_->GetColor(0);
    device_.SetColor(RGBGetRValue(c), RGBGetGValue(c), RGBGetBValue(c));
}

void BloodyP93Plugin::DeviceUpdateLEDs(void* obj)
{
    static_cast<BloodyP93Plugin*>(obj)->ApplyColor();
}

void BloodyP93Plugin::DeviceUpdateZoneLEDs(void* obj, int)
{
    static_cast<BloodyP93Plugin*>(obj)->ApplyColor();
}

void BloodyP93Plugin::DeviceUpdateSingleLED(void* obj, int)
{
    static_cast<BloodyP93Plugin*>(obj)->ApplyColor();
}

QWidget* BloodyP93Plugin::GetWidget() { return widget_; }
QMenu* BloodyP93Plugin::GetTrayMenu() { return nullptr; }

void BloodyP93Plugin::Unload()
{
    enabled_.store(false);
    if(controller_ != nullptr && api_ != nullptr)
    {
        api_->UnregisterVirtualRGBController(controller_);
        api_->DeleteVirtualRGBController(controller_);
        controller_ = nullptr;
    }
    device_.Close();
}

void BloodyP93Plugin::OnProfileAboutToLoad() {}
void BloodyP93Plugin::OnProfileLoad(nlohmann::json) {}
nlohmann::json BloodyP93Plugin::OnProfileSave() { return nlohmann::json::object(); }

unsigned char* BloodyP93Plugin::OnSDKCommand(unsigned int, unsigned char*, unsigned int* size)
{
    if(size) { *size = 0; }
    return nullptr;
}

void BloodyP93Plugin::ProfileManagerUpdated(unsigned int) {}
void BloodyP93Plugin::ResourceManagerUpdated(unsigned int) {}
void BloodyP93Plugin::SettingsManagerUpdated(unsigned int) {}
