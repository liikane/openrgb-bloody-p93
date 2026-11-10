#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#endif
#include "BloodyP93Plugin.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QFont>
#include <QPushButton>
#include <QCheckBox>
#include <QSettings>
#include <QVariant>
#include <QStringList>
#include <QSet>
#include <QSignalBlocker>
#include <array>

namespace
{
QVariant LoadSetting(const char* key, const QVariant& fallback)
{
    QSettings settings(QSettings::IniFormat, QSettings::UserScope, "liikane", "OpenRGBBloodyP93Plugin");
    return settings.value(QString::fromLatin1(key), fallback);
}

void SaveSetting(const char* key, const QVariant& value)
{
    QSettings settings(QSettings::IniFormat, QSettings::UserScope, "liikane", "OpenRGBBloodyP93Plugin");
    settings.setValue(QString::fromLatin1(key), value);
    settings.sync();
}
}

OpenRGBPluginInfo BloodyP93Plugin::GetPluginInfo()
{
    OpenRGBPluginInfo info{};
    info.Name = "True Mouse Art";
    info.Description = "Bloody P93 mouse OpenRGB Plugin / I Turned My Mouse into a Flashing Beacon!";
    info.Version = "0.3.0";
    info.Commit = "community";
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
    enabled_.store(false);
    widget_ = new QWidget();
    auto* layout = new QVBoxLayout(widget_);
    auto* title = new QLabel("True Mouse Art / Bloody P93 mouse OpenRGB Plugin", widget_);
    QFont font = title->font();
    font.setBold(true);
    title->setFont(font);
    layout->addWidget(title);
    auto* tagline = new QLabel("I Turned My Mouse into a Flashing Beacon!", widget_);
    layout->addWidget(tagline);

    status_ = new QLabel("Checking Bloody P93 HID device...", widget_);
    status_->setWordWrap(true);
    layout->addWidget(status_);

    enable_ = new QCheckBox("Enable RGB control (experimental)", widget_);
    enable_->setEnabled(false);
    layout->addWidget(enable_);

    auto* retry = new QPushButton("Retry device detection", widget_);
    layout->addWidget(retry);

    auto* separator = new QLabel("Eight physical P93 LEDs, mapped to the first eight HID RGB slots.", widget_);
    separator->setWordWrap(true);
    layout->addWidget(separator);

    auto* identify = new QPushButton("Identify next LED slot (yellow)", widget_);
    layout->addWidget(identify);
    slot_status_ = new QLabel("Physical LEDs: 1 wheel, 2 left front, 3 right front, 4 extra buttons, 5 right mid, 6 left mid, 7 left rear, 8 right rear. Logo: 7+8.", widget_);
    layout->addWidget(slot_status_);

    auto* restore = new QPushButton("Restore selected OpenRGB colors", widget_);
    layout->addWidget(restore);

    auto* form = new QFormLayout();
    left_slots_ = new QLineEdit("1,4", widget_);
    right_slots_ = new QLineEdit("2,3,5,6,7,8", widget_);
    interval_ = new QSpinBox(widget_);
    interval_->setRange(120, 2000);
    interval_->setSingleStep(50);
    interval_->setValue(320);
    interval_->setSuffix(" ms");
    form->addRow("Beacon group A (slot numbers)", left_slots_);
    form->addRow("Beacon group B (slot numbers)", right_slots_);
    form->addRow("Beacon interval", interval_);
    layout->addLayout(form);

    beacon_ = new QCheckBox("Flashing beacon — alternate groups A and B (yellow)", widget_);
    beacon_->setEnabled(false);
    layout->addWidget(beacon_);

    notifications_ = new QCheckBox("Enable local notification commands (127.0.0.1:45893)", widget_);
    notifications_->setEnabled(false);
    layout->addWidget(notifications_);

    auto* instructions = new QLabel(
        "Windows only. 64-byte HID RGB reports, no button macros or firmware changes. "
        "The HID report contains 15 slots, but only slots 1-8 connect to P93 lighting. "
        "Notification commands are listened for only when enabled. "
        "Unchecking RGB control stops effects but may leave the last color on the mouse.", widget_);
    instructions->setWordWrap(true);
    layout->addWidget(instructions);
    layout->addStretch(1);

    beacon_timer_ = new QTimer(this);
    beacon_timer_->setInterval(interval_->value());
    connect(beacon_timer_, &QTimer::timeout, this, [this]{ TickBeacon(); });

    notification_timeout_ = new QTimer(this);
    notification_timeout_->setSingleShot(true);
    connect(notification_timeout_, &QTimer::timeout, this, [this]{
        if(beacon_) beacon_->setChecked(false);
        ApplyColor();
    });

    notification_poller_ = new QTimer(this);
    notification_poller_->setInterval(60);
    connect(notification_poller_, &QTimer::timeout, this, [this]{ HandleNotification(); });

    color_persistence_timer_ = new QTimer(this);
    color_persistence_timer_->setSingleShot(true);
    color_persistence_timer_->setInterval(700);
    connect(color_persistence_timer_, &QTimer::timeout, this, [this]{
        if(!pending_colors_.isEmpty())
            SaveSetting("lastColors", pending_colors_);
    });

    connect(enable_, &QCheckBox::toggled, this, [this](bool value){
        SaveSetting("rgbEnabled", value);
        enabled_.store(value);
        beacon_->setEnabled(value);
        notifications_->setEnabled(value);
        if(!value)
        {
            notification_timeout_->stop();
            beacon_->setChecked(false);
            notifications_->setChecked(false);
            status_->setText("Bloody P93 connected. RGB writes disabled; the last color may remain.");
        }
        else
        {
            status_->setText("RGB control enabled. Use Devices for individual slots, or start the beacon.");
            ApplyColor();
        }
    });

    connect(interval_, qOverload<int>(&QSpinBox::valueChanged), this, [this](int val){
        beacon_timer_->setInterval(val);
        SaveSetting("intervalMs", val);
    });

    connect(beacon_, &QCheckBox::toggled, this, [this](bool checked){
        if(checked && enabled_.load())
        {
            beacon_phase_ = false;
            beacon_timer_->start(interval_->value());
            TickBeacon();
        }
        else
        {
            beacon_timer_->stop();
            if(enabled_.load()) ApplyColor();
        }
    });

    connect(identify, &QPushButton::clicked, this, [this]{
        if(!enabled_.load()) return;
        notification_timeout_->stop();
        beacon_->setChecked(false);
        P93Protocol::Slots slot_colors{};
        slot_colors[static_cast<std::size_t>(next_slot_)] = {255,210,0};
        if(device_.SetSlots(slot_colors))
        {
            slot_status_->setText(QString("Active physical LED: %1/8. Check the mouse lighting.")
                .arg(next_slot_ + 1));
            next_slot_ = (next_slot_ + 1) % 8;
        }
        else
        {
            status_->setText("Cannot send slot test. Retry device detection.");
        }
    });

    connect(restore, &QPushButton::clicked, this, [this]{
        notification_timeout_->stop();
        beacon_->setChecked(false);
        ApplyColor();
    });

    connect(notifications_, &QCheckBox::toggled, this, [this](bool enabled){
        SaveSetting("notificationsEnabled", enabled);
        if(!enabled)
        {
            StopNotificationListener();
            return;
        }
        if(!enabled_.load() || !StartNotificationListener())
        {
            notifications_->setChecked(false);
            status_->setText("Could not listen on 127.0.0.1:45893 (port unavailable).");
        }
        else
        {
            status_->setText("Local notification listener active on 127.0.0.1:45893.");
        }
    });

    connect(retry, &QPushButton::clicked, this, [this]{
        if(controller_ == nullptr)
        {
            RegisterDevice();
            return;
        }
        enable_->setChecked(false);
        device_.Close();
        std::string error;
        if(device_.Connect(error))
        {
            enable_->setEnabled(true);
            status_->setText("Bloody P93 reconnected. Enable RGB control to apply colors.");
        }
        else
        {
            enable_->setEnabled(false);
            status_->setText(QString::fromStdString(error));
        }
    });

    // Restore preferences only after signals and the controller are registered.
    // On first installation, RGB control remains off until the user opts in.
    left_slots_->setText(LoadSetting("groupA", QStringLiteral("1,4")).toString());
    right_slots_->setText(LoadSetting("groupB", QStringLiteral("2,3,5,6,7,8")).toString());
    {
        std::vector<std::size_t> a, b;
        if(!ParseGroups(a,b))
        {
            left_slots_->setText("1,4");
            right_slots_->setText("2,3,5,6,7,8");
            SaveSetting("groupA", left_slots_->text());
            SaveSetting("groupB", right_slots_->text());
        }
    }
    interval_->setValue(LoadSetting("intervalMs", 320).toInt());
    connect(left_slots_, &QLineEdit::editingFinished, this, [this]{
        SaveSetting("groupA", left_slots_->text().trimmed());
    });
    connect(right_slots_, &QLineEdit::editingFinished, this, [this]{
        SaveSetting("groupB", right_slots_->text().trimmed());
    });

    RegisterDevice();
    if(enable_->isEnabled() && LoadSetting("rgbEnabled", false).toBool())
    {
        enable_->setChecked(true);
        if(LoadSetting("notificationsEnabled", false).toBool())
            notifications_->setChecked(true);
    }
}

bool BloodyP93Plugin::ParseGroups(std::vector<std::size_t>& left,
                                  std::vector<std::size_t>& right)
{
    auto parse = [](const QString& text, std::vector<std::size_t>& out) {
        const auto items = text.split(',', Qt::SkipEmptyParts);
        if(items.empty()) return false;
        QSet<int> used;
        for(const QString& entry : items)
        {
            bool ok = false;
            const int value = entry.trimmed().toInt(&ok);
            if(!ok || value < 1 || value > 8 || used.contains(value))
                return false;
            used.insert(value);
            out.push_back(static_cast<std::size_t>(value-1));
        }
        return true;
    };
    if(!parse(left_slots_->text(), left) || !parse(right_slots_->text(), right))
        return false;
    for(std::size_t l : left)
        for(std::size_t r : right)
            if(l == r) return false;
    return true;
}

void BloodyP93Plugin::TickBeacon()
{
    if(!enabled_.load() || !beacon_->isChecked()) return;
    std::vector<std::size_t> a, b;
    if(!ParseGroups(a,b))
    {
        beacon_->setChecked(false);
        status_->setText("Invalid beacon groups: use non-overlapping physical LED numbers 1-8.");
        return;
    }

    P93Protocol::Slots slot_colors{};
    for(std::size_t i : (beacon_phase_ ? b : a))
        slot_colors[i] = beacon_color_;
    beacon_phase_ = !beacon_phase_;
    if(!device_.SetSlots(slot_colors))
    {
        beacon_->setChecked(false);
        status_->setText("Beacon HID write failed. Retry device detection.");
    }
}

bool BloodyP93Plugin::StartNotificationListener()
{
#ifdef _WIN32
    if(notification_socket_handle_ != ~std::uintptr_t{0})
        return true;

    WSADATA winsock{};
    if(WSAStartup(MAKEWORD(2, 2), &winsock) != 0)
        return false;

    const SOCKET socketHandle = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if(socketHandle == INVALID_SOCKET)
    {
        WSACleanup();
        return false;
    }
    u_long nonblocking = 1;
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(45893);
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if(ioctlsocket(socketHandle, FIONBIO, &nonblocking) != 0 ||
       bind(socketHandle, reinterpret_cast<const sockaddr*>(&address), sizeof(address)) == SOCKET_ERROR)
    {
        closesocket(socketHandle);
        WSACleanup();
        return false;
    }

    notification_socket_handle_ = static_cast<std::uintptr_t>(socketHandle);
    notification_poller_->start();
    return true;
#else
    return false;
#endif
}

void BloodyP93Plugin::StopNotificationListener()
{
    if(notification_poller_)
        notification_poller_->stop();
#ifdef _WIN32
    if(notification_socket_handle_ != ~std::uintptr_t{0})
    {
        closesocket(static_cast<SOCKET>(notification_socket_handle_));
        notification_socket_handle_ = ~std::uintptr_t{0};
        WSACleanup();
    }
#endif
}

void BloodyP93Plugin::HandleNotification()
{
#ifdef _WIN32
    if(notification_socket_handle_ == ~std::uintptr_t{0})
        return;

    const SOCKET socketHandle = static_cast<SOCKET>(notification_socket_handle_);
    for(;;)
    {
        std::array<char, 64> packet{};
        const int length = recvfrom(socketHandle, packet.data(), static_cast<int>(packet.size()), 0, nullptr, nullptr);
        if(length == SOCKET_ERROR)
        {
            if(WSAGetLastError() != WSAEWOULDBLOCK)
                status_->setText("Local notification socket read failed.");
            break;
        }
        if(length <= 0 || !enabled_.load() || !notifications_->isChecked())
            continue;

        const QByteArray cmd = QByteArray(packet.data(), length).trimmed().toUpper();
        if(cmd == "P93:SUCCESS")
        {
            notification_timeout_->stop();
            beacon_->setChecked(false);
            P93Protocol::Slots slot_colors{};
            for(std::size_t i=0; i<P93Protocol::PhysicalLedCount; ++i)
                slot_colors[i] = {0, 255, 0};
            if(device_.SetSlots(slot_colors))
                notification_timeout_->start(1800);
        }
        else if(cmd == "P93:ALERT" || cmd == "P93:ERROR" || cmd == "P93:NOTICE")
        {
            beacon_color_ = cmd == "P93:ERROR" ? P93Protocol::Color{255, 0, 0}
                                             : P93Protocol::Color{255, 210, 0};
            if(!beacon_->isChecked())
                beacon_->setChecked(true);
            notification_timeout_->start(5000);
        }
        else if(cmd == "P93:STOP")
        {
            notification_timeout_->stop();
            beacon_->setChecked(false);
            ApplyColor();
        }
    }
#endif
}

void BloodyP93Plugin::RegisterDevice()
{
    if(api_ == nullptr || controller_ != nullptr) return;

    std::string error;
    if(!device_.Connect(error))
    {
        status_->setText(QString::fromStdString(error));
        enable_->setEnabled(false);
        return;
    }

    RGBController_Setup setup{};
    setup.description = "True Mouse Art: eight physical LED zones and a programmable mouse beacon.";
    setup.location = "HID 09DA:31DE MI_02 COL04";
    setup.name = "Bloody P93 (community)";
    setup.vendor = "Bloody";
    setup.version = "0.3.0";
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
    all.name = "P93 physical LEDs (1-8)";
    all.type = ZONE_TYPE_LINEAR;
    all.start_idx = 0;
    all.leds_count = P93Protocol::PhysicalLedCount;
    all.leds_min = P93Protocol::PhysicalLedCount;
    all.leds_max = P93Protocol::PhysicalLedCount;
    setup.zones.push_back(all);

    for(std::size_t i=0;i<P93Protocol::PhysicalLedCount;++i)
    {
        led slot{};
        static const char* names[P93Protocol::PhysicalLedCount] = {
            "1 - Wheel", "2 - Left front", "3 - Right front",
            "4 - Extra buttons center", "5 - Right middle",
            "6 - Left middle", "7 - Left rear + logo",
            "8 - Right rear + logo"
        };
        slot.name = names[i];
        slot.value = static_cast<unsigned int>(i);
        setup.leds.push_back(slot);
    }

    setup.object_ptr = this;
    setup.DeviceUpdateLEDs = &BloodyP93Plugin::DeviceUpdateLEDs;
    setup.DeviceUpdateZoneLEDs = &BloodyP93Plugin::DeviceUpdateZoneLEDs;
    setup.DeviceUpdateSingleLED = &BloodyP93Plugin::DeviceUpdateSingleLED;

    controller_ = api_->CreateVirtualRGBController(&setup);
    if(!controller_)
    {
        status_->setText("Failed to create OpenRGB virtual controller.");
        device_.Close();
        return;
    }

    const QStringList remembered = LoadSetting("lastColors", QStringList{}).toStringList();
    for(std::size_t i=0;i<P93Protocol::PhysicalLedCount;++i)
    {
        unsigned red=160, green=0, blue=255;
        if(i < static_cast<std::size_t>(remembered.size()))
        {
            const auto components = remembered.at(static_cast<qsizetype>(i)).split(',');
            if(components.size()==3)
            {
                bool validR=false, validG=false, validB=false;
                const unsigned rr=components[0].toUInt(&validR);
                const unsigned gg=components[1].toUInt(&validG);
                const unsigned bb=components[2].toUInt(&validB);
                if(validR && validG && validB && rr <= 255 && gg <= 255 && bb <= 255)
                { red=rr; green=gg; blue=bb; }
            }
        }
        controller_->SetColor(static_cast<unsigned int>(i), ToRGBColor(red,green,blue));
    }
    api_->RegisterVirtualRGBController(controller_);
    status_->setText("Bloody P93 connected. RGB writes disabled until you enable them.");
    enable_->setEnabled(true);
}

void BloodyP93Plugin::ApplyColor()
{
    if(!enabled_.load() || !controller_ || (beacon_ && beacon_->isChecked()))
        return;

    P93Protocol::Slots slot_colors{};
    QStringList colorPreferences;
    for(std::size_t i=0;i<P93Protocol::PhysicalLedCount;++i)
    {
        const RGBColor color = controller_->GetColor(static_cast<unsigned int>(i));
        const unsigned red = static_cast<unsigned>(RGBGetRValue(color));
        const unsigned green = static_cast<unsigned>(RGBGetGValue(color));
        const unsigned blue = static_cast<unsigned>(RGBGetBValue(color));
        slot_colors[i] = {
            static_cast<std::uint8_t>(red),
            static_cast<std::uint8_t>(green),
            static_cast<std::uint8_t>(blue)
        };
        colorPreferences << QStringLiteral("%1,%2,%3").arg(red).arg(green).arg(blue);
    }
    pending_colors_ = colorPreferences;
    color_persistence_timer_->start();
    if(!device_.SetSlots(slot_colors))
    {
        enabled_.store(false);
        QMetaObject::invokeMethod(this, [this]{
            if(enable_) enable_->setChecked(false);
            if(status_) status_->setText("RGB write failed. Check mouse connection and retry detection.");
        }, Qt::QueuedConnection);
    }
}

void BloodyP93Plugin::DeviceUpdateLEDs(void* self) { static_cast<BloodyP93Plugin*>(self)->ApplyColor(); }
void BloodyP93Plugin::DeviceUpdateZoneLEDs(void* self, int) { static_cast<BloodyP93Plugin*>(self)->ApplyColor(); }
void BloodyP93Plugin::DeviceUpdateSingleLED(void* self, int) { static_cast<BloodyP93Plugin*>(self)->ApplyColor(); }

QWidget* BloodyP93Plugin::GetWidget() { return widget_; }
QMenu* BloodyP93Plugin::GetTrayMenu() { return nullptr; }

void BloodyP93Plugin::Unload()
{
    if(color_persistence_timer_ && color_persistence_timer_->isActive() && !pending_colors_.isEmpty())
    {
        color_persistence_timer_->stop();
        SaveSetting("lastColors", pending_colors_);
    }
    enabled_.store(false);
    if(beacon_timer_) beacon_timer_->stop();
    if(notification_timeout_) notification_timeout_->stop();
    StopNotificationListener();
    if(controller_ && api_)
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
    if(size) *size = 0;
    return nullptr;
}
void BloodyP93Plugin::ProfileManagerUpdated(unsigned int) {}
void BloodyP93Plugin::ResourceManagerUpdated(unsigned int) {}
void BloodyP93Plugin::SettingsManagerUpdated(unsigned int) {}
