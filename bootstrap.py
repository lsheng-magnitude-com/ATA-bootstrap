from __future__ import print_function

import glob
import os
import shutil
import stat
import subprocess
import sys
import traceback


def main(argv):
    upperEnvVariables()
    setP4Env()
    p4exe = getP4Exe()
    branch = getBoosterBranch()
    boosterLongLabel = getBoosterLabel()
    print('booster core label = ' + boosterLongLabel)
    configLongLabel = getConfigFileLabel()
    print('booster project config file label = ' + configLongLabel)
    (boosterLabel, boosterChangelists) = parseLabel(boosterLongLabel)
    (configLabel, configChangelists) = parseLabel(configLongLabel)
    boosterDepot = getBoosterDepot(branch)
    configDepot = getConfigDepot(branch)
    #propsFile = getPropsFile()
    revert(p4exe, '//...')
    #revert(boosterDepot)
    clean_repo(p4exe, branch)
    syncLabel(p4exe, boosterDepot, boosterLabel)
    syncLabel(p4exe, configDepot, configLabel)
    #syncPropsFile(p4exe, propsFile, configLabel)
    #SyncLabel(p4exe, propsFile, configLabel)
    for cl in boosterChangelists:
        unshelve(p4exe, cl, boosterDepot)
    for cl in configChangelists:
        unshelve(p4exe, cl, boosterDepot)
        #if propsFile != 'undef':
        #    unshelve(p4exe, cl, propsFile)
    if len(argv) != 0:
        buildfile = argv[0]
        syncLabel(p4exe, buildfile, configLabel)
        for cl in configChangelists:
            unshelve(p4exe, cl, buildfile)
    elif os.environ.get('BAMBOO_BOOSTER_CONFIG_REPO','') != '':
        config_repo = '//' + os.environ['BAMBOO_BOOSTER_CONFIG_REPO'] + '/...'
        syncLabel(p4exe, config_repo, configLabel)
        for cl in configChangelists:
            unshelve(p4exe, cl, config_repo)


def setP4Env():
    setP4Port()
    setP4USER()
    setP4Client()


def setP4Port():
    os.environ['P4PORT'] = os.environ['BAMBOO_P4PORT']


def setP4USER():
    os.environ['P4USER'] = os.environ['BAMBOO_SEN_P4USERNAME']


def setP4Client():
    agentName = os.environ['BAMBOO_CAPABILITY_ORG_HOSTNAME']
    if os.environ['BAMBOO_ATA_BAMBOO_SERVER'] == '2':
        clientName = 'bamboo_sen_' + agentName
    else:
        clientName = 'bamboo_' + agentName
    os.environ['P4CLIENT'] = clientName


def getP4Exe():
    p4Exe = '"' + os.environ.get('BAMBOO_CAPABILITY_SYSTEM_P4EXECUTABLE', 'p4') + '"'
    return p4Exe


def getBoosterBranch():
    return os.environ.get('BAMBOO_BOOSTER_BRANCH', 'Maintenance/1.0')


def getBoosterLabel():
    booster_stable_label = os.environ.get('BAMBOO_BOOSTER_STABLE_LABEL', 'head')
    booster_label = os.environ.get('BAMBOO_BOOSTER_LABEL', '__latest__')
    if booster_label == 'stable' or booster_label == '__latest__':
        return booster_stable_label
    else:
        booster_label = booster_label.replace('__latest', 'latest')
        booster_label = booster_label.replace('latest', booster_stable_label)
        return booster_label


def getConfigFileLabel():
    configFileLabel = os.environ.get('BAMBOO_PRODUCT_LABEL', 'BAMBOO_BOOSTER_LABEL')
    return os.environ.get(configFileLabel, 'head')


def getBoosterDepot(branch):
    return '//ATA/Booster/' + branch + '/...'


def getConfigDepot(branch):
    return '//ATA/Booster/' + branch + '/Config/Projects/...'


def getPropsFile():
    propsFile = os.environ.get('PROPS_FILE', 'undef')
    branchPath = os.environ.get('BAMBOO_BRANCH_PATH', 'ATA/Placeholder')
    if propsFile != 'undef':
        return '//' + propsFile
    elif branchPath != 'ATA/Placeholder':
        if branchPath.startswith('SimbaEngine'):
            return '//' + branchPath + '/Product/Solutions/SEN_settings.props'
        elif branchPath.startswith('SimbaTestTools/Touchstone'):
            return '//' + branchPath + '/Touchstone_settings.props'
        else:
            return '//' + branchPath + '/Product/Source/driver.props'
    else:
        return 'undef'


def syncPropsFile(p4exe, file, label):
    if file == 'undef':
        print ('No props file defined')
    else:
        syncLabel(p4exe, file, label)


def syncHead(p4exe, depot):
    command = p4exe + ' sync -f ' + depot + '#head'
    ExecuteAndGetResult(command)


def syncLabel(p4exe, depot, label):
    if label == 'head':
        print('use head of ' + depot)
        syncHead(p4exe, depot)
    else:
        if isInLabel(p4exe, depot, label):
            command = p4exe + ' sync -f ' + depot + '@' + label
            ExecuteAndGetResult(command)
        else:
            print(depot + ' not in ' + label + '. Use head instead')
            syncHead(p4exe, depot)


def unshelve(p4exe, changelist, path):
    """
    unshelve the specified path to the changelist
    """
    if changelist is not None and changelist != '':
        command = p4exe + ' unshelve -s ' + changelist + ' ' + path
        try:
            ExecuteAndGetResult(command)
        except subprocess.CalledProcessError as error:
            sys.stdout.flush()
            print(error.output)
            print("Changelist " + changelist + " does not exist")
            exit(-1)


def revert(p4exe, path):
    command = p4exe + ' revert ' + path
    ExecuteAndGetResult(command)


def clean_repo(p4exe, branch):
    """ Resets the booster repo to revision 0 and cleanup the booster directory """
    # sync using -f flag to force remove files that were unshelved which leaves them open for edit
    command = p4exe + ' sync -f //ATA/Booster/{branch}/...#0'.format(branch=branch)
    ExecuteAndGetResult(command)
    # remove any unremoved files and the booster branch directory
    booster_dir = os.path.normpath(os.path.join(os.getcwd(), os.path.pardir, branch))
    print("Cleaning up directory {}".format(booster_dir))
    remove_dir(booster_dir)
    #clean up other major depots
    command = p4exe + ' sync -f //Drivers/...#0'
    ExecuteAndGetWarning(command)
    command = p4exe + ' sync -f //SimbaEngine/...#0'
    ExecuteAndGetResult(command)
    command = p4exe + ' sync -f //SimbaShared/...#0'
    ExecuteAndGetResult(command)
    command = p4exe + ' sync -f //ThirdParty/...#0'
    ExecuteAndGetResult(command)
    command = p4exe + ' sync -f //Insight/...#0'
    ExecuteAndGetResult(command)


def isInLabel(p4exe, file, label):
    command = p4exe + ' files ' + file + '@' + label
    result = ExecuteAndGetResult(command)
    result = result.decode('utf-8')
    if 'no such file' in result:
        return False
    else:
        return True


def parseLabel(longLabel):
    longLabel = longLabel.replace('__head__CL', 'head__CL')
    longLabel = longLabel.replace('__head__', 'head')
    longLabel = longLabel.replace('__CL', '__')
    labelArray = longLabel.split('__')
    if 'head' in longLabel:
        return labelArray[0], labelArray[1:]
    else:
        return labelArray[0], labelArray[1:]


def ExecuteAndGetResult(command):
    print(command)
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        return result
    except subprocess.CalledProcessError as error:
        sys.stdout.flush()
        print(error.output)
        raise


def ExecuteAndGetWarning(command):
    print(command)
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        return result
    except subprocess.CalledProcessError as error:
        sys.stdout.flush()
        print("Warning=====")
        print(error.output)
        print("============")



def upperEnvVariables():
    for key in os.environ.keys():
        os.environ[key.upper()] = os.environ[key]


def remove_dir(dir):
    if os.path.isdir(dir):
    	# remove directory's contents
        for item in glob.glob(dir + '/*'):
            try:
                if os.path.isfile(item): remove_single_file(item)
                if os.path.islink(item): remove_single_file(item)
                if os.path.isdir(item): remove_dir(item)
            except Exception:
                print('Failed to Remove %s' % item)
                continue
        for item in glob.glob(dir + '/.*'):
            try:
                if os.path.isfile(item): remove_single_file(item)
                if os.path.islink(item): remove_single_file(item)
                if os.path.isdir(item): remove_dir(item)
            except Exception:
                print('Failed to Remove %s' % item)
                continue
        # remove the directory once its contents have been removed
        try:
            shutil.rmtree(dir)
        except Exception as e:
            print(e)
            try:
                os.rmdir(dir)
                print("symlink removed using rmdir instead")
            except Exception as e:
                # still fail to delete, resort to continuing
                print("*******************************")
                print("failed to remove %s, continuing" % dir)
                print("*******************************")
                print(str(e))


def remove_single_file(file):
    if os.path.isfile(file):
    	# change the permission of the file
        try:
            os.chmod(file, stat.S_IWRITE)
        except Exception:
            print('Failed to change the file permission to writable - %s' % file)
            pass
        os.remove(file)
    if os.path.islink(file):
        os.remove(file)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception:
        traceback.print_exc()
        exit(-1)
