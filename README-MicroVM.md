Create MicroVM-ISO :- 

* Install Ubuntu18.04

* git clone https://github.com/CacheboxInc/linux-live.git in /tmp

* MicroVM :-
   
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
   - Reboot machine and verify microvm service
   
* Live ISO :-

   - You will need the following packages to be installed:
      - squashfs-tools
      - genisoimage or mkisofs
      - zip
      - xorriso
   - ./build
   - New ISO will available at /tmp

* To create vm on vCenter use script create_vm.py

