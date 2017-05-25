# coding: utf-8
#!/usr/bin/env python
import yaml
import os
import io
import sys
import tarfile
import ConfigParser
import shutil

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

current_dir=os.path.dirname(os.path.realpath(__file__))

#------------------------------CONFIG SECTION------------------------------
# File Locations(Change will make in these files)
yaml_locations={"rosco" : "/opt/rosco/config/rosco.yml",
                "orca" : "/opt/spinnaker/config/orca.yml",
                "spinnaker-local" : "/opt/spinnaker/config/spinnaker-local.yml"
               }
js_locations={"deck_setting_js" : "/opt/spinnaker/config/settings.js",
              "setting_js" : "/opt/deck/html/settings.js",
              "app_js" : "/opt/deck/html/app.js",
              "packer_sh" : "/opt/rosco/config/packer/install_packages.sh"
             }

#AWS Credentials
aws_access_key_id="AKIAICDLWL4PVK563DXQ"
aws_secret_access_key="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"
# Change "aws_credential_path" path, if you need any other location
aws_credential_path=os.path.join(os.path.expanduser("~"), ".aws/credentials")

# Changes to the files(These are the changes apply to config files)
updates={"rosco_configdir" : "/opt/rosco/config/packer",
         "orca_baseurl" : "http://edge8:8090",
         "debianRepository": "http://jenkinsn42.s3-website-us-west-2.amazonaws.com trusty main",
         "netflixMode": "true",
         "jenikins_baseURL" : "http://172.25.30.10:8080"
         }
#--------------------------END OF CONFIG SECTION--------------------------

def check_pre_installtion():
    for names, locations in yaml_locations.items():
        if not os.path.exists(locations):
            print Colors.FAIL+"{} not found. Aboring Configuration.".format(locations)+Colors.ENDC
            exit(1)
    for names, locations in js_locations.items():
        if not os.path.exists(locations):
            print Colors.FAIL+"{} not found. Aboring Configuration.".format(locations)+Colors.ENDC
            exit(1)
    print Colors.OKBLUE+"+ All config files available....[ OK ]"+Colors.OKBLUE

def create_backup_file(file_location):
    if os.path.exists(file_location+".backup"):
        return
    else:
        os.rename(file_location,file_location+".backup")

def createAWSCerd():
    config = ConfigParser.ConfigParser()
    config.set(ConfigParser.DEFAULTSECT,"aws_access_key_id",aws_access_key_id)
    ORIG_DEFAULTSECT = ConfigParser.DEFAULTSECT
    ConfigParser.DEFAULTSECT = 'default'
    config.set("default","aws_secret_access_key",aws_secret_access_key)
    try:
        os.makedirs(os.path.dirname(aws_credential_path))
    except:pass
    with open(aws_credential_path, 'w') as configfile:
        config.write(configfile)
    print Colors.OKBLUE+"+ AWS credentials file created.{}".format(aws_credential_path)+Colors.ENDC

def read_yaml(file_name):
    if not os.path.exists(file_name):
        print Colors.FAIL+"{} not found! Please check.".format(file_name)+Colors.ENDC
        exit(1)
    with open(file_name) as f:
        data=yaml.load(f)
    return data

def write_yaml(data,yaml_file):
    #make a backup file and write
    print Colors.OKBLUE+"+ Updating {}".format(yaml_file)+Colors.ENDC
    create_backup_file(yaml_file)
    with io.open(yaml_file, 'w', encoding='utf8') as outfile:
        yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)

def set_true():# This is for setting "netflixMode" true in .js setting files
    for name, file_location in js_locations.items():
        if not os.path.exists(file_location):
            print Colors.FAIL+"{} not found! Please check.".format(file_location)+Colors.ENDC
            exit(1)
        lines=list()
        with open(file_location,"r") as f:
            for line in f.readlines():
                if "netflixMode: false" in line:
                    lines.append("netflixMode: {},\n".format(updates["netflixMode"]))
                else:
                    lines.append(line)
        #make backup file and write
        create_backup_file(file_location)
        print Colors.OKBLUE+"+ Updating {}".format(file_location)+Colors.ENDC
        create_backup_file(file_location)
        with open(file_location,"w") as f:
            f.writelines(lines)

def spinnaker_local_copy():# It is common in both cases(Install form backup & install from git)
    print Colors.OKBLUE+"+ Copying {} to /home/spinnaker/.spinnaker/spinnaker-local.yml".format(yaml_locations['spinnaker-local'])+Colors.ENDC
    try:
        os.makedirs("/home/spinnaker/.spinnaker")
    except:pass
    shutil.copyfile(yaml_locations['spinnaker-local'], "/home/spinnaker/.spinnaker/spinnaker-local.yml")
    os.chmod("/home/spinnaker/.spinnaker/spinnaker-local.yml",0600)

def install_from_backup():
    print Colors.HEADER+"\n**** Installing Spinnaker From Backup ****"+Colors.ENDC
    print Colors.WARNING+"IMPORTANT NOTE: Please remove/backup the previous versions of spinnaker in '/opt/'"+Colors.ENDC
    while 1:
        tar_location=raw_input("Please enter backup .tar file location>")
        if not os.path.exists(tar_location):
            print Colors.FAIL+"File location not found, try again\n"+Colors.ENDC
            continue
        break
    tarfile.open(tar_location)
    print "Extracting tar file.."
    tarfile.extractall("/opt/")
    createAWSCerd()
    config=read_yaml(yaml_locations['spinnaker-local'])
    config['services']['jenkins']['defaultMaster']['baseUrl']=updates['jenikins_baseURL']
    write_yaml(config,yaml_locations['spinnaker-local'])
    spinnaker_local_copy()

def install_from_git():
    print Colors.HEADER+"\n**** Installing Spinnaker From GIT Repo ****"+Colors.ENDC
    #Step-1
    os.system("git clone https://github.com/spinnaker/spinnaker.git /opt/spinnaker")
    os.system("bash /opt/spinnaker/InstallSpinnaker.sh")
    check_pre_installtion()
    #Step-2
    createAWSCerd()
    spinnaker_local_copy()
    #Step-5,Change1
    rosco=read_yaml(yaml_locations["rosco"])
    rosco['rosco']['configDir']=updates["rosco_configdir"]
    rosco['debianRepository']=updates["debianRepository"]
    create_backup_file(yaml_locations["rosco"])
    write_yaml(rosco, yaml_locations["rosco"])
    '''
    #Change2
    orca=read_yaml(yaml_locations["orca"])
    orca['mine']['baseUrl']=updates["orca_baseurl"]
    create_backup_file(yaml_locations["orca"])
    write_yaml(orca, yaml_locations["orca"])
    '''
    #Change3
    set_true()
    #Change4
    print Colors.OKBLUE+"+ Updating {}".format(js_locations["app_js"])+Colors.ENDC
    if not os.path.exists(js_locations["app_js"]):
        print Colors.FAIL+"{} not found. Exiting installation at Step-5, Change-4"+Colors.ENDC
        exit(1)
    with open(js_locations["app_js"],'r') as f:
        new_lines=list()
        for line in f.readlines():
            if "‘titus’, ‘instance.detailsTemplateUrl’" in line:
                new_lines.append("// "+line)
            else:
                new_lines.append(line)
    create_backup_file(js_locations["app_js"])
    with open(js_locations["app_js"],"w") as f:
        f.writelines(new_lines)
    #Change5
    print Colors.OKBLUE+"+ Updating {}".format(js_locations["packer_sh"])+Colors.ENDC
    with open(js_locations["packer_sh"],'r') as f:
        new_lines=list()
        for line in f.readlines():
            if "for package in $packages; do sudo apt-get install --force-yes -y $package; done" in line:
                new_lines.append(line)
                new_lines.append("sudo apt-get install -y wget curl")
                new_lines.append("sudo apt-get install -y python-pip python-dev build-essential")
                new_lines.append("sudo wget -O packer_installer.sh https://goo.gl/kK8YPM && sudo chmod 777 packer_installer.sh && sudo sh packer_installer.sh")
            else:
                new_lines.append(line)
    create_backup_file(js_locations["packer_sh"])
    with open(js_locations["packer_sh"],"w") as f:
        f.writelines(new_lines)

    print Colors.OKGREEN+"\nSpinnaker Configuration Completed!"+Colors.ENDC
    print Colors.WARNING+"---------------------------INFO---------------------------"
    print "Scripts Location".ljust(20," "),"/opt/spinnaker/scripts/"
    print "To Start".ljust(20," "),"./start_spinnaker.sh"
    print "To Stop".ljust(20," "),"./stop_spinnaker.sh"
    print "To Reconfigure".ljust(20," "),"./reconfigure_spinnaker.sh"
    print "\nssh  -i spinnaker.pem -L 9000:127.0.0.1:9000 -L 8084:127.0.0.1:8084 -L 8087:127.0.0.1:8087 ubuntu@spinnakerip"
    print "URL".ljust(20," "),"http://localhost:9000"+Colors.ENDC

if __name__=='__main__':
    if not os.geteuid() == 0:
        print "Script must run with 'sudo'"
        exit(1)
    while 1:
        res=raw_input("\nPlease select one option below.\n1. Install from git repo(Latest Release)\n2. Install from backup(Backup .tar file needed)\n>")
        if res.strip()=="1":
            install_from_git()
            exit()
        elif res.strip()=="2":
            install_from_backup()
            exit()
        else:
            print "Invalid option. Please try again"
