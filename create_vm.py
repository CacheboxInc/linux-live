#!/usr/bin/env python

"""

Run script cmd :-  python3.6 create_vm.py -s 192.168.10.122 
                                          -u administrator@vsphere.local 
                                          -p Root@123 
                                          -d OC_Datastore 
                                          -datacenter OC_Datacenter
                                          -folder 'vm' -Rpool OC_RPool  
                                          -vmname mz -nw 'VM Network'
                                          -iso_path 'microVM-IP.iso'

"""

import atexit

from pyVim import connect
from pyVmomi import vim
from pyVim.task import WaitForTask

from tools import cli, tasks

try:
    input = raw_input
except NameError:
    pass

def get_args():
    parser = cli.build_arg_parser()

    parser.add_argument('-d', '--datastore',
                        required=True,
                        help='Name of Datastore to create VM in')

    parser.add_argument('-datacenter',
                        required=True,
                        help='Name of the datacenter to create VM in.')

    parser.add_argument('-folder',
                        required=True,
                        help='Name of the vm folder to create VM in.')

    parser.add_argument('-Rpool',
                        required=True,
                        help='Name of resource pool to create VM in.')

    parser.add_argument('-vmname',
                         required=True,
                         help='Name of VM to create')

    parser.add_argument('-nw',
                        required=True,
                        help='Name of network.')
    
    parser.add_argument('-iso_path',
                        required=True,
                        help='ISO path.')

    args = parser.parse_args()

    return cli.prompt_for_password(args)

def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
            content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def create_dummy_vm(vm_name, service_instance, vm_folder, resource_pool, datastore, guestId):
    datastore_path = '[' + datastore + '] ' + vm_name

    # bare minimum VM shell, no disks. Feel free to edit
    vmx_file = vim.vm.FileInfo(logDirectory=None,
                               snapshotDirectory=None,
                               suspendDirectory=None,
                               vmPathName=datastore_path)

    # For EFI boot add firmware='EFI'
    config = vim.vm.ConfigSpec(name=vm_name, memoryMB=2048, numCPUs=2,
                               files=vmx_file, guestId=guestId,
                               version='vmx-13')
    
    print("\nCreating VM {}...".format(vm_name))
    task = vm_folder.CreateVM_Task(config=config, pool=resource_pool)
    tasks.wait_for_tasks(service_instance, [task])
    tasks.wait_for_tasks(service_instance, [task])

def find_free_ide_controller(vm):
    for dev in vm.config.hardware.device:
        if isinstance(dev, vim.vm.device.VirtualIDEController):
            # If there are less than 2 devices attached, we can use it.
            if len(dev.device) < 2:
                return dev
    return None

def add_nic(si, vm, network_name):
    spec = vim.vm.ConfigSpec()
    nic_changes = []
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic_spec.device = vim.vm.device.VirtualE1000()
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.deviceInfo.summary = 'vCenter API test'
    content = si.RetrieveContent()
    network = get_obj(content, [vim.Network], network_name)
    if isinstance(network, vim.OpaqueNetwork):
        nic_spec.device.backing = \
                vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()

        nic_spec.device.backing.opaqueNetworkType = \
                network.summary.opaqueNetworkType
        nic_spec.device.backing.opaqueNetworkId = \
                network.summary.opaqueNetworkId
    else:
        nic_spec.device.backing = \
                vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.useAutoDetect = False
        nic_spec.device.backing.deviceName = network.name

    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.connectable.connected = False
    nic_spec.device.connectable.status = 'untried'
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.addressType = 'assigned'

    nic_changes.append(nic_spec)
    spec.deviceChange = nic_changes
    e = vm.ReconfigVM_Task(spec=spec)
    print("NIC Card added")

def new_cdrom_spec(controller_key, backing):
    connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    connectable.allowGuestControl = True
    connectable.startConnected = True
    
    cdrom = vim.vm.device.VirtualCdrom()
    cdrom.controllerKey = controller_key
    cdrom.key = -1
    cdrom.connectable = connectable
    cdrom.backing = backing
    return cdrom

def get_physical_cdrom(host):
    for lun in host.configManager.storageSystem.storageDeviceInfo.scsiLun:
        if lun.lunType == 'cdrom':
            return lun
    return None

def find_device(vm, device_type):
    result = []
    for dev in vm.config.hardware.device:
        if isinstance(dev, device_type):
            result.append(dev)
    return result

def attach_iso(si, datastore, args, vm_name, boot=True):
    dc = si.content.rootFolder.childEntity[0]
    vm = si.content.searchIndex.FindChild(dc.vmFolder, vm_name)

    spec = vim.vm.device.VirtualDeviceSpec()
    spec.device = vim.vm.device.VirtualCdrom()
    spec.device.key = -1
    spec.device.unitNumber = 0

    controller = find_free_ide_controller(vm)
    if controller:
        spec.device.controllerKey = controller.key
    else:
        print("Could not find a free IDE controller "
                "on '%s' to attach ISO '%s'", args.vmname, iso_path)
        return

    spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
    spec.device.backing.fileName = "[%s] %s" % (args.datastore, args.iso_path)
    spec.device.backing.datastore = datastore
    
    spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    spec.device.connectable.allowGuestControl = True
    spec.device.connectable.startConnected = True

    spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    vm_spec = vim.vm.ConfigSpec(deviceChange=[spec])
    
    if boot:  
        print("Setting {} to boot from ISO {}".format(args.vmname, args.iso_path))
        order = [vim.vm.BootOptions.BootableCdromDevice()]
        order.extend(list(vm.config.bootOptions.bootOrder))
        vm_spec.bootOptions = vim.vm.BootOptions(bootOrder=order)
     
    WaitForTask(vm.Reconfigure(vm_spec))
    print("Added cd-drive")
    power_on(vm)

def power_on(vm):
    print("Power On VM ...")
    WaitForTask(vm.PowerOn())
    print("--------------------")

def delete_vms():
    parser = cli.build_arg_parser()
    
    parser.add_argument('-vmname',
            required=True,
            help='Name of VM to create')

    args = parser.parse_args()

    si = connect_host(args)
    name = args.vmname
    dc = si.content.rootFolder.childEntity[0]
    
    os_types = ["ubuntuGuest", "ubuntu64Guest", "windows8Server64Guest", \
                "windows9Server64Guest", "rhel6Guest", "rhel6_64Guest", \
                "rhel7_64Guest", "sles12_64Guest", "centos7_64Guest","winLonghornGuest"]

    for os in os_types :
        vm_name = name + "-" + os
        vm = si.content.searchIndex.FindChild(dc.vmFolder, vm_name)
        print("\nPower off {} ..".format(vm_name))
        WaitForTask(vm.PowerOffVM_Task())
        
        print("Deleting vm {}...".format(vm_name))
        WaitForTask(vm.Destroy_Task())

def connect_host(args):
    si = connect.SmartConnectNoSSL(host=args.host,
                                                 user=args.user,
                                                 pwd=args.password,
                                                 port=int(args.port))
    if not si:
        print("Could not connect using specified username and password")
        return -1
    print("Connected to vCenter")
    atexit.register(connect.Disconnect, si)
    return si

def main():
    args = get_args()
    service_instance = connect_host(args) 
    
    content = service_instance.RetrieveContent()
    vmfolder = get_obj(content, [vim.Folder], args.folder)
    resource_pool = get_obj(content, [vim.ResourcePool], args.Rpool)


    datastore = get_obj(content, [vim.Datastore], args.datastore) 

    os_types = ["ubuntuGuest", "ubuntu64Guest", "windows8Server64Guest", \
                "windows9Server64Guest", "rhel6Guest", "rhel6_64Guest", \
                "rhel7_64Guest", "sles12_64Guest", "centos7_64Guest","winLonghornGuest"]
    vm = None
    for os in os_types :
        vm_name = args.vmname + "-" + os
        create_dummy_vm(vm_name, service_instance, vmfolder, resource_pool,
                        args.datastore, os)
        
        vm = get_obj(content, [vim.VirtualMachine], vm_name)
        add_nic(service_instance, vm, args.nw)
        attach_iso(service_instance, datastore, args, vm_name)

if __name__ == "__main__":
    main()
