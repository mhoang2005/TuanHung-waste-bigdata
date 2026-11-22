"""Create task-local VMware guests from verified Fedora Cloud image."""
from pathlib import Path
import subprocess
import hashlib

ROOT = Path(__file__).resolve().parents[2]
VMROOT = Path(r"C:\Users\OS\Documents\WasteLabVMs")
VMROOT.mkdir(parents=True, exist_ok=True)
image = ROOT / "work/downloads/fedora44.qcow2"
expected = "28680fe5b371a5a82ebf43a31926e086a168e59949d03969c5093e7071f90b7f"
assert hashlib.file_digest(image.open("rb"), "sha256").hexdigest() == expected
pubkey = (ROOT / "work/keys/lab_ed25519.pub").read_text().strip()

def wslpath(path):
    return "/mnt/" + str(path)[0].lower() + str(path)[2:].replace("\\", "/")

def linux(*args):
    subprocess.run(["wsl", "-d", "Ubuntu-22.04", "-u", "root", "--", *args], check=True)

base = VMROOT / "fedora-base.vmdk"
if not base.exists():
    linux("qemu-img", "resize", wslpath(image), "64G")
    linux("qemu-img", "convert", "-p", "-f", "qcow2", "-O", "vmdk", "-o", "subformat=monolithicSparse", wslpath(image), wslpath(base))

for i, ram in [(1, 3072), (2, 2560), (3, 2560)]:
    node = VMROOT / f"vm{i}"
    node.mkdir(exist_ok=True)
    disk = node / "disk.vmdk"
    if not disk.exists():
        import shutil
        shutil.copy2(base, disk)
    mac = f"00:50:56:30:00:{10+i:02d}"
    (node / "meta-data").write_text(f"instance-id: waste-vm{i}\nlocal-hostname: waste-vm{i}\n", encoding="utf-8")
    (node / "user-data").write_text(f"""#cloud-config
hostname: waste-vm{i}
manage_etc_hosts: true
users:
  - name: lab
    groups: [wheel]
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: true
    ssh_authorized_keys:
      - {pubkey}
ssh_pwauth: false
disable_root: true
growpart:
  mode: auto
  devices: ['/']
resize_rootfs: true
""", encoding="utf-8")
    (node / "network-config").write_text(f"""version: 1
config:
  - type: physical
    name: eth0
    mac_address: '{mac}'
    subnets:
      - type: static
        address: 192.168.200.{10+i}/24
        gateway: 192.168.200.2
        dns_nameservers: [192.168.200.2]
""", encoding="utf-8")
    linux("genisoimage", "-quiet", "-output", wslpath(node / "seed.iso"), "-volid", "cidata", "-joliet", "-rock", *[wslpath(node / x) for x in ["user-data", "meta-data", "network-config"]])
    (node / f"waste-vm{i}.vmx").write_text(f'''config.version = "8"
virtualHW.version = "21"
displayName = "Waste Big Data VM{i} Fedora44"
guestOS = "other5xlinux-64"
firmware = "efi"
memsize = "{ram}"
numvcpus = "2"
cpuid.coresPerSocket = "2"
scsi0.present = "TRUE"
scsi0.virtualDev = "lsisas1068"
scsi0:0.present = "TRUE"
scsi0:0.fileName = "disk.vmdk"
sata0.present = "TRUE"
sata0:1.present = "TRUE"
sata0:1.deviceType = "cdrom-image"
sata0:1.fileName = "seed.iso"
ethernet0.present = "TRUE"
ethernet0.connectionType = "nat"
ethernet0.virtualDev = "e1000e"
ethernet0.addressType = "static"
ethernet0.address = "{mac}"
uuid.action = "create"
tools.syncTime = "TRUE"
msg.autoAnswer = "TRUE"
gui.viewModeAtPowerOn = "minimized"
''', encoding="utf-8")
    print(node / f"waste-vm{i}.vmx")
