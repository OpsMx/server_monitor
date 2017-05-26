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
aws_access_key_id=""
aws_secret_access_key=""
# Change "aws_credential_path" path, if you need any other location
aws_credential_path=os.path.join(os.path.expanduser("~"), ".aws/credentials")
aws_credential_path2="/home/spinnaker/.aws/credentials"

# Changes to the files(These are the changes apply to config files)
updates={"rosco_configdir" : "/opt/rosco/config/packer",
         "orca_baseurl" : "http://172.9.239.142:8090",
         "debianRepository": "http://jenkinsn42.s3-website-us-west-2.amazonaws.com trusty main",
         "netflixMode": "true",
         "jenikins_baseURL" : "http://172.9.239.142:8080",
         "defaultRegion" : "${SPINNAKER_AWS_DEFAULT_REGION:us-west-2}",
         "Credentials-name" : "GopinathRebala",
         "defaultIAMRole" : "BaseIAMRole"
         }
#--------------------------END OF CONFIG SECTION--------------------------

def Pre_Installation_Checks():
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
    global aws_access_key_id, aws_secret_access_key
    while 1:
        if not aws_access_key_id:
            aws_access_key_id=raw_input("AWS KEY Not Found. Please enter>")
        if not aws_secret_access_key:
            aws_secret_access_key=raw_input("AWS Secret Access Not Found. Please enter>")
        if aws_access_key_id and aws_secret_access_key:
            break
        else:
            print Colors.FAIL+"Invalid Inputs. Please Try Again\n"+Colors.ENDC
    config = ConfigParser.ConfigParser()
    config.set(ConfigParser.DEFAULTSECT,"aws_access_key_id",aws_access_key_id)
    ORIG_DEFAULTSECT = ConfigParser.DEFAULTSECT
    ConfigParser.DEFAULTSECT = 'default'
    config.set("default","aws_secret_access_key",aws_secret_access_key)
    try:
        os.makedirs(os.path.dirname(aws_credential_path))
    except:pass
    try:
        os.makedirs(os.path.dirname(aws_credential_path2))
    except:pass
    with open(aws_credential_path, 'w') as configfile:
        config.write(configfile)
    print Colors.OKBLUE+"+ AWS credentials file created.{}".format(aws_credential_path)+Colors.ENDC
    with open(aws_credential_path2,'w') as f:
        config.write(configfile)
    print Colors.OKBLUE+"+ AWS credentials file created.{}".format(aws_credential_path2)+Colors.ENDC

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

def MakeConfigurations():
    print Colors.BOLD+"****************CONFIGURING SPINNAKER****************"+Colors.ENDC
    Pre_Installation_Checks()
    #Step-2
    createAWSCerd()

    config=read_yaml(yaml_locations['spinnaker-local'])
    config['services']['jenkins']['defaultMaster']['baseUrl']=updates['jenikins_baseURL']
    config['services']['jenkins']['enabled']=True
    config['services']['igor']['enabled']=True
    config['providers']['aws']['defaultIAMRole']=updates['defaultIAMRole']
    config['providers']['aws']['enabled']=True
    config['providers']['aws']['primaryCredentials']['name']=updates['Credentials-name']
    config['providers']['aws']['defaultRegion']=updates['defaultRegion']
    try:
        del config['providers']['aws']['defaultKeyPairTemplate']
    except:pass
    write_yaml(config,yaml_locations['spinnaker-local'])
    spinnaker_local_copy()
    #Step-5,Change1
    rosco=read_yaml(yaml_locations["rosco"])
    rosco['rosco']['configDir']=updates["rosco_configdir"]
    rosco['debianRepository']=updates["debianRepository"]
    write_yaml(rosco, yaml_locations["rosco"])

    #Change2
    orca=read_yaml(yaml_locations["orca"])
    orca['mine']={'baseUrl' : updates["orca_baseurl"]}
    create_backup_file(yaml_locations["orca"])
    write_yaml(orca, yaml_locations["orca"])

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

def Spinnaker_Download():
    print Colors.BOLD+"****************DOWNLOADING SPINNAKER FORM GIT****************"+Colors.ENDC
    os.system("git clone https://github.com/spinnaker/spinnaker.git /opt/spinnaker")
    os.system("bash /opt/spinnaker/InstallSpinnaker.sh")

if __name__=='__main__':
    if not os.geteuid() == 0:
        print "Script must run with 'sudo'"
        exit(1)
    while 1:
        res=raw_input("\nDo you want to download Spinnaker from GIT?[y/n]>")
        if res.strip().lower()=="y":
            Spinnaker_Download()
            MakeConfigurations()
            break
        elif res.strip().lower()=="n":
            MakeConfigurations()
            break
        else:
            print Colors.FAIL+"Invalid Option. Please Try Again"+Colors.ENDC
