# Create MicroVM-ISO :- 

* Create VM and attach mini_ubuntu.iso http://192.168.1.177/5TB_NFS/ISO/mini_ubuntu18.04.iso
* Perform installation
* apt install open-vm-tools, openssh-server, lssci
* add following in "/etc/netplan/01-netcfg.yaml"
    ethernets:
      all:
        match:
          name: ens*
        dhcp4: yes
        dhcp-identifier: mac
   
* Create clone of this VM
* git clone https://github.com/Aukshan-PIO/open-vm-tools.git and 
* git clone https://github.com/CacheboxInc/linux-live.git in /tmp
* Build procedure open-vm-tools

# MicroVM :-
   
   - Copy microvm binary in /bin directory
   - Copy all dependencies from tools/dependancies to /usr/lib
   - Try to execute microvm binary.
   - cd MicroVM
   - cp ip.sh micro.sh  /root
   - cp microservice.service  /etc/systemd/system/microservice.service 
   - chmod +x ip.sh micro.sh /etc/systemd/system/microservice.service
   - systemctl start microservice.service
   - systemctl status microservice.service
   - systemctl enable microservice.service
   - Add photon ssh key for passwordless ssh
   - Reboot machine and verify microvm service

# open-vm-tools

* The default open-vm-tools does a reboot of the VM during guest customization. This is a problem because we cannot persist the changes when booting from ISO. We are only interested in the network configuration and not the other functionality provided by cloud-init. For this reason we have modified open-vm-tools not to reboot after the guest-customization. The step below is the procedure to configure this.
* Make a clone of the Ubuntu18.04 on which we will install the compilation environment. We won't do it directly on the MicroVM as it will bloat the size. Instead we build on a different VM and copy the final .so files. All steps below are on the clone.
* git clone https://github.com/CacheboxInc/open-vm-tools.git
* git checkout stable-11.0.5
* install open-vm-tools/bionic-updates,now 2:11.0.5-4ubuntu0.18.04.1
* apt install autoconf libxmlsec1-dev  libxml2-dev  libglib2.0-dev libmspack-dev libpam0g-dev libx11-dev libtool libxext-dev libxinerama-dev libxi-dev libxrender-dev libxrandr-dev libgdk-pixbuf2.0-dev libgtk-3-dev libgtkmm-2.4-dev libgtkmm-3.0-dev
* follow the build procedure in README of open-vm-tools
* the configure script will
* ./configure --disable-multimon --without-x  --without-kernel-modules
* make / make install (follow the README)
* now copy cp /usr/local/lib/libDeployPkg.so.0.0 on MICRO-VM:/usr/lib/libDeployPkg.so.0.0

# Live ISO :-

   - You will need the following packages to be installed:
      - squashfs-tools
      - genisoimage or mkisofs
      - zip
      - xorriso
   - ./build
   - New ISO will available at /tmp

* To create vm on vCenter use script create_vm.py

