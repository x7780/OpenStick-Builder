# OpenStick 镜像构建工具
适用于基于 MSM8916 的 4G 调制解调器 USB 网卡的镜像构建工具

本构建工具使用由 [postmarketOS](https://postmarketos.org/) 为高通 MSM8916 设备提供的预编译[内核](https://pkgs.postmarketos.org/package/v24.06/postmarketos/aarch64/linux-postmarketos-qcom-msm8916)。

> [!NOTE]
> 此分支生成 `alpine` 镜像，如需 `debian` 镜像请使用 [main 分支](https://github.com/kinsamanka/OpenStick-Builder/tree/main)。

## 构建说明
### 本地构建
已在 **Ubuntu 22.04** 上测试通过
- 克隆仓库
  ```shell
  git clone -b alpine --recurse-submodules https://github.com/kinsamanka/OpenStick-Builder.git
  cd OpenStick-Builder/
  ```
#### 快速构建
- 构建
  ```shell
  cd OpenStick-Builder/
  sudo ./build.sh
  ```
#### 详细步骤
- 安装依赖
  ```shell
  sudo scripts/install_deps.sh
  ```
- 构建 hyp 和 lk2nd

  这些自定义引导加载程序支持 `extlinux.conf` 文件的基本功能，类似于 u-boot 和 depthcharge。
  ```shell
  sudo scripts/build_hyp_aboot.sh
  ```
- 提取高通固件

  提取引导加载程序并创建新的分区表，充分利用 eMMC 的全部空间。
  ```shell
  sudo scripts/extract_fw.sh
  ```
- 创建根文件系统
  ```shell
  sudo scripts/alpine_rootfs.sh
  ```
- 创建镜像
  ```shell
  sudo scripts/build_images.sh
  ```

生成的固件文件将保存在 `files` 目录下。

### 通过 Github Actions 在云端构建
1. Fork 本仓库
2. 运行 [Build workflow](../../actions/workflows/build.yml)
   - 点击并运行 ***Run workflow***
   - 工作流完成后，点击工作流摘要，然后下载生成的构件

## 自定义
编辑 [`scripts/alpine_rootfs.sh`](scripts/alpine_rootfs.sh#L33) 以添加或删除软件包。

## 固件安装
> [!WARNING]  
> 以下命令可能导致设备变砖，使其无法启动。请谨慎操作，风险自负！

> [!IMPORTANT]  
> 请务必先使用命令 `edl rf orig_fw.bin` 备份原始固件！

### 前置条件
- [EDL](https://github.com/bkerler/edl)
- Android fastboot 工具
  ```
  sudo apt install fastboot
  ```

### 步骤
- 参照此[教程](https://wiki.postmarketos.org/wiki/Zhihe_series_LTE_dongles_(generic-zhihe)#How_to_enter_flash_mode)进入高通 EDL 模式
- 备份必要分区

  需要从原始固件中提取以下文件：
  
     - `fsc.bin`
     - `fsg.bin`
     - `modem.bin`
     - `modemst1.bin`
     - `modemst2.bin`
     - `persist.bin`
     - `sec.bin`

  如果这些文件已存在，可跳过此步骤。
  ```shell
  for n in fsc fsg modem modemst1 modemst2 persist sec; do
      edl r ${n} ${n}.bin
  done
  ```
- 安装 `aboot`
  ```shell
  edl w aboot aboot.mbn
  ```
- 重启进入 fastboot 模式
  ```shell
  edl e boot
  edl reset
  ```
- 刷入固件
  ```shell
  fastboot flash partition gpt_both0.bin
  fastboot flash aboot aboot.mbn
  fastboot flash hyp hyp.mbn
  fastboot flash rpm rpm.mbn
  fastboot flash sbl1 sbl1.mbn
  fastboot flash tz tz.mbn
  fastboot flash boot boot.bin
  fastboot flash rootfs alpine_rootfs.bin
  ```
- 恢复原始分区
  ```shell
  for n in fsc fsg modem modemst1 modemst2 persist sec; do
      fastboot flash ${n} ${n}.bin
  done
  ```
- 重启
  ```shell
  fastboot reboot
  ```

## 安装后配置
- 网络配置
  
  | wlan0 | |
  | ----- | ---- |
  | SSID | Openstick |
  | 密码 | openstick |
  | IP 地址 | 192.168.43.1 |

  | usb0 | |
  | ----- | ---- |
  | IP 地址 | 192.168.42.1 |

- 默认用户
  
  | | |
  | ----- | ---- |
  | 用户名 | root |
  | 密码 | root |
 
- 如果你的设备不是基于 **UZ801**，请修改 `/boot/extlinux/extlinux.conf` 以使用正确的设备树：
  ```shell
  sed -i 's/yiming-uz801v3/<BOARD>/' /boot/extlinux/extlinux.conf
  ```

  其中 `<BOARD>` 对应：
     - `thwc-uf896` 对应 **UF896** 板型
     - `thwc-ufi001c` 对应 **UFIxxx** 板型
     - `jz01-45-v33` 对应 **JZxxx** 板型
     - `fy-mf800` 对应 **MF800** 板型

- 扩展 `rootfs` 分区至最大容量：
  ```shell
  resize2fs /dev/disk/by-partlabel/rootfs
  ```
