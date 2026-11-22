# Bước 1 — Mở VM1 và xác nhận Fedora/mạng/SSH

Mục tiêu của bước này: vào được terminal Fedora của **VM1** từ Windows. Chỉ làm với một VM trước để giảm áp lực RAM và xác định cấu hình guest thực tế.

## 1. Dùng đúng bộ VM đã có

Lần đọc máy ngày 22/10/2026 tìm thấy ba bộ file tại:

```text
C:\Users\OS\Documents\WasteLabVMs\vm1\waste-vm1.vmx
C:\Users\OS\Documents\WasteLabVMs\vm2\waste-vm2.vmx
C:\Users\OS\Documents\WasteLabVMs\vm3\waste-vm3.vmx
```

Theo script `project/infra/create_vms.py`, các đĩa được tạo từ Fedora Cloud và đi kèm `seed.iso` để cloud-init cấu hình người dùng, SSH và mạng lần đầu. Chưa khởi động guest trong lần hướng dẫn này, nên cần xác nhận khả năng boot và nhận seed thực tế.

Bộ này độc lập với VM `Fedora44-Lab` cũ đang khai báo 8 GiB RAM. Sử dụng các đường dẫn trên cho cụm dự án.

Cloud image được chuẩn bị để đăng nhập bằng **SSH key**, tài khoản `lab`. Trong cấu hình seed, đăng nhập bằng mật khẩu bị khóa. Nếu console hiện màn hình hỏi login, hãy thực hiện bước SSH bên dưới.

## 2. Giảm tải host trước khi bật máy

Host có khoảng 15,7 GiB RAM và lúc quan sát chỉ còn khoảng 2,3 GiB trống. VM1 đang được khai báo 3 GiB; VMware và Windows cũng cần bộ nhớ.

Đóng bớt ứng dụng hoặc workload không cần dùng bằng cách bình thường, rồi xem lại mục **Memory** trong Task Manager. Ban đầu chỉ bật VM1. Chưa tự động thay RAM/CPU hay dừng ứng dụng nào trong bước này.

## 3. Mở VM1 bằng VMware

1. Mở VMware Workstation.
2. Chọn **File -> Open**.
3. Mở `C:\Users\OS\Documents\WasteLabVMs\vm1\waste-vm1.vmx`.
4. Trong phần cấu hình, xác nhận máy có 3 GiB RAM, 2 vCPU, Network Adapter dùng **NAT**, ổ đĩa `disk.vmdk` và CD/DVD trỏ tới `seed.iso`.
5. Bật **Power on** và để quá trình khởi động lần đầu hoàn thành.

Lần đầu cloud-init có thể cần thêm thời gian để tạo tài khoản, áp dụng cấu hình mạng và SSH. Nếu VMware báo lỗi trước khi Fedora boot, giữ nguyên nội dung lỗi để xử lý đúng nguyên nhân.

## 4. Địa chỉ dự kiến của mạng lab

Địa chỉ host/gateway được đọc từ cấu hình VMware đang có; các IP guest là cấu hình dự kiến từ seed.

| Thành phần | Địa chỉ |
|---|---|
| Windows, VMnet8 | `192.168.200.1/24` |
| Gateway và DNS NAT | `192.168.200.2` |
| VM1 | `192.168.200.11/24` |
| VM2 | `192.168.200.12/24` |
| VM3 | `192.168.200.13/24` |

Dải DHCP VMnet8 đang là `.128` đến `.254`; ba địa chỉ guest dự kiến nằm ngoài dải cấp động đó. Sau khi guest boot vẫn phải xác nhận IP đã được áp dụng.

## 5. SSH từ PowerShell trên Windows

SSH key đã tồn tại tại đường dẫn dùng trong lệnh sau. Mở PowerShell và chạy:

```powershell
ssh -i "C:\Users\OS\Documents\ChatGPT\Tiểu luận big data\work\keys\lab_ed25519" lab@192.168.200.11
```

Nếu hiện thông báo xác nhận danh tính máy lần đầu, đối chiếu đúng VM1/IP của lab trước khi chấp nhận. Thành công khi vào được shell của tài khoản `lab` trên guest.

Nếu không vào được:

- `Connection timed out`: ghi lại lỗi và màn hình VMware; cần xem VM đã boot, NIC có kết nối và guest có nhận IP hay chưa.
- `Connection refused`: máy đích trả lời nhưng dịch vụ SSH chưa sẵn sàng hoặc chưa được khởi động; chờ khởi tạo hoàn tất rồi xem tình trạng guest.
- `Permission denied (publickey)`: cần xác định seed có được cloud-init nhận và tài khoản/key có được tạo không.
- Lỗi quyền truy cập private key từ Windows: gửi nguyên văn lỗi quyền; không phải lỗi Kafka hay Spark.

## 6. Ghi lại tình trạng Fedora

Sau khi SSH thành công, chạy từng lệnh trong shell Fedora:

```bash
cat /etc/os-release
```

```bash
hostnamectl --static
```

```bash
ip -br address
```

```bash
free -h
```

```bash
df -h /
```

```bash
cloud-init status
```

Kết quả cần xác nhận: Fedora và phiên bản thực tế, hostname dự kiến `waste-vm1`, địa chỉ `192.168.200.11`, RAM/disk và cloud-init có hoàn tất hay đang lỗi.

Chưa cài Hadoop/Kafka/Spark trước khi giải quyết được bước đăng nhập và địa chỉ guest.

## 7. Sau VM1

Khi đã rõ VM1 hoạt động, làm tương tự cho VM2/VM3, thay đường dẫn VM và IP trong lệnh SSH tương ứng. Có thể làm tuần tự từng máy, tắt guest bằng `sudo poweroff` sau khi ghi lại thông tin nếu host chưa đủ RAM cho cả ba.

Sau đó mới thống nhất hostname/IP giữa ba guest, truy cập mạng giữa chúng và ngân sách RAM/CPU trước chặng cài Java/HDFS/YARN.

## Nguồn về cloud-init

- [Fedora: gói cloud-init](https://packages.fedoraproject.org/pkgs/cloud-init/cloud-init/)
- [Canonical: NoCloud và seed chứa user-data/meta-data/network-config](https://github.com/canonical/cloud-init/blob/main/doc/rtd/reference/datasources/nocloud.rst)

Tình trạng trong hướng dẫn là quan sát từ host và file cấu hình; chưa phải xác nhận đăng nhập guest thành công.
