# 5G Network Emulator GUI

Aplikasi GUI untuk mendesain dan menjalankan emulasi jaringan 5G secara visual dengan fitur drag and drop.

## Features

- **Visual Topology Designer**: Drag and drop komponen 5G
- **Real-time Configuration**: Edit konfigurasi komponen secara langsung
- **Connection Management**: Buat koneksi antar komponen dengan mudah
- **Export Capabilities**: Generate Mininet script dan Docker Compose
- **Live Emulation**: Jalankan emulasi langsung dari GUI
- **Save/Load Projects**: Simpan dan buka proyek topologi

## Komponen 5G yang Tersedia

### Core Network
- **AMF** (Access and Mobility Management Function)
- **SMF** (Session Management Function)
- **UPF** (User Plane Function)
- **NRF** (Network Repository Function)
- **UDM** (Unified Data Management)
- **UDR** (Unified Data Repository)
- **PCF** (Policy Control Function)
- **AUSF** (Authentication Server Function)

### RAN (Radio Access Network)
- **gNB** (5G NodeB / Base Station)
- **UE** (User Equipment)

### Network Infrastructure
- **Switch** (Network Switch)
- **Router** (Network Router)

## Installation

### Prerequisites

```bash
# Install Python 3.8+
python --version

# Install tkinter (biasanya sudah termasuk)
# Pada Ubuntu/Debian:
sudo apt-get install python3-tk

# Install dependencies tambahan
pip install pillow
```

### Install Mininet-WiFi (untuk emulasi)

```bash
# Clone Mininet-WiFi
git clone https://github.com/intrig-unicamp/mininet-wifi
cd mininet-wifi
sudo util/install.sh -Wlnfv
```

### Install Docker (untuk deployment)

```bash
# Pada Ubuntu/Debian:
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker $USER
```

## Usage

### Menjalankan Aplikasi

```bash
cd Project_5g
python 5g_emulator_gui.py
```

### Basic Operations

1. **Menambah Komponen**
   - Klik tombol komponen di panel kiri
   - Komponen akan ditambahkan ke canvas
   - Atau drag komponen ke posisi yang diinginkan

2. **Mengedit Komponen**
   - Double-click komponen untuk edit konfigurasi
   - Ubah nama dan parameter konfigurasi
   - Konfigurasi dalam format JSON

3. **Membuat Koneksi**
   - Klik tombol "Connection Mode"
   - Klik komponen pertama, lalu komponen kedua
   - Atau klik kanan komponen → "Connect"

4. **Menggerak Komponen**
   - Click dan drag komponen untuk memindahkan
   - Koneksi akan mengikuti pergerakan komponen

5. **Context Menu**
   - Klik kanan pada komponen untuk menu:
     - Edit: Edit konfigurasi
     - Delete: Hapus komponen
     - Connect: Mulai mode koneksi

### Keyboard Shortcuts

- `Ctrl+N`: New topology
- `Ctrl+O`: Open topology
- `Ctrl+S`: Save topology
- `Ctrl+Shift+S`: Save As

### Export dan Deployment

1. **Export Mininet Script**
   - File → Export Mininet Script
   - Generate script Python untuk Mininet-WiFi
   - Jalankan dengan: `sudo python script.py`

2. **Export Docker Compose**
   - File → Export Docker Compose
   - Generate file docker-compose.yml
   - Deploy dengan: `docker-compose up -d`

3. **Live Emulation**
   - Run → Start Emulation
   - Emulasi langsung menggunakan Mininet
   - Memerlukan sudo privileges

### File Management

- **Save Project**: File → Save (format JSON)
- **Load Project**: File → Open
- **New Project**: File → New

## Example Topologies

### Basic 5G Network

1. Tambahkan komponen core: AMF, SMF, UPF, NRF
2. Tambahkan gNB dan UE
3. Hubungkan:
   - UE → gNB
   - gNB → Switch → UPF
   - UPF → SMF → AMF
   - Semua core components → NRF

### Multi-Cell Network

1. Tambahkan multiple gNB dan UE
2. Buat central UPF
3. Hubungkan semua gNB ke UPF
4. Distribusikan UE ke berbagai gNB

## Configuration Examples

### UE Configuration
```json
{
  "imsi": "999700000000001",
  "key": "465B5CE8B199B49FAA5F0A2EE238A6BC",
  "opc": "E8ED289DEBA952E4283B54E88E6183CA"
}
```

### gNB Configuration
```json
{
  "mcc": "999",
  "mnc": "70",
  "nci": 1,
  "tac": 1,
  "linkIp": "127.0.0.1",
  "ngapIp": "127.0.0.1",
  "gtpIp": "127.0.0.1"
}
```

### AMF Configuration
```json
{
  "plmn_id": {
    "mcc": "999",
    "mnc": "70"
  },
  "port": 7777,
  "tai": {
    "tac": 1
  }
}
```

## Troubleshooting

### Common Issues

1. **Permission Denied saat Start Emulation**
   ```bash
   # Jalankan dengan sudo atau add user ke group
   sudo python 5g_emulator_gui.py
   ```

2. **Mininet Command Not Found**
   ```bash
   # Install mininet-wifi
   git clone https://github.com/intrig-unicamp/mininet-wifi
   cd mininet-wifi
   sudo util/install.sh -Wlnfv
   ```

3. **Docker Permission Denied**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   # Logout and login again
   ```

4. **tkinter Import Error**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-tk
   
   # CentOS/RHEL
   sudo yum install tkinter
   ```

### Debug Mode

Untuk debugging, jalankan dengan verbose output:
```bash
python 5g_emulator_gui.py --debug
```

## Advanced Features

### Custom Components

Anda bisa menambahkan komponen custom dengan mengedit file:
```python
# Dalam ComponentLibrary.COMPONENTS, tambahkan:
'CUSTOM_COMPONENT': {
    'name': 'Custom Component Name',
    'color': '#HEXCOLOR',
    'icon': '🔧',
    'default_config': {
        'param1': 'value1',
        'param2': 'value2'
    }
}
```

### Integration dengan Existing Scripts

GUI ini dapat diintegrasikan dengan script Mininet yang sudah ada:
1. Load topologi existing dengan mengkonversi ke format JSON
2. Export dari GUI ke format yang compatible
3. Gunakan sebagai frontend untuk script yang kompleks

## Contributing

Untuk berkontribusi:
1. Fork repository
2. Buat feature branch
3. Commit changes
4. Push ke branch
5. Create Pull Request

## License

Project ini untuk keperluan research dan edukasi.

## Support

Jika ada pertanyaan atau issues:
1. Check troubleshooting section
2. Check existing issues di repository
3. Create new issue dengan detail lengkap

## Roadmap

### Planned Features
- [ ] 3D visualization mode
- [ ] Network performance monitoring
- [ ] Automated topology optimization
- [ ] Integration dengan real 5G testbeds
- [ ] Machine learning for topology recommendation
- [ ] Real-time traffic simulation
- [ ] Multi-user collaboration
- [ ] Cloud deployment support
