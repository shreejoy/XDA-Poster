import os
import hashlib
import requests
import subprocess
from github import Github

auth = Github("$USERNAME", "$PASSWORD")

def runSh(command):
    try:
        command = command.split(' ')
        command = filter(None, command)
        command = list(command)
        if not len(command):
            raise Exception("Not a valid command.")
        subprocess.call(command)
    except Exception as e:
        print(f"runSh failed:", e)


def runShAndReturnStdout(command):
    try:
        command = command.split(' ')
        command = filter(None, command)
        command = list(command)
        if not len(command):
            raise Exception("Not a valid command.")
        proc = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = proc.stdout.read().decode()
        return output
    except Exception as e:
        print(f"runShAndReturnStdout failed:", e)


def auth_request(url, method='POST', data={}, validResponseCodes=200, validResponseContent='OK', ReturnStdout=False):
    req = requests.post if method == 'POST' else requests.get
    headers = {'web-api-key': API_KEY}
    response = req(url, data, headers=headers)

    if validResponseCodes != response.status_code:
        raise Exception(
            f"Cannot get a validate the status code for the requested resource.\n\nExpected {validResponseCode} and recieved {response.status_text}")

    if validResponseContent:
        if validResponseContent != response.text:
            raise Exception(
                f"Cannot get a validate the output result for the requested resource.\n\nExpected {validResponseContent} and recieved {response.text}")

    if ReturnStdout:
        return response

def logUpload():
    org_name = "PixysOS-Devices"
    repo_name = "jenkins_console"
    org = auth.get_organization(org_name)
    repo = org.get_repo(repo_name)
    try:
        release = repo.create_git_release("$uid", "$BUILD_NUMBER", f"Console text for build number #$BUILD_NUMBER")
        release.upload_asset("release/build.log")
    except:
        pass

def buildUpload(resp):
    value = 0
    device = resp['device']
    filehash = resp['filehash']
    timestamp = resp['timestamp']

    org_name = hashlib.md5("pixys-releases".encode('utf-8')).hexdigest()
    repo_name = hashlib.md5(device.encode('utf-8')).hexdigest()
    org = auth.get_organization(org_name)

    try:
        repo = org.get_repo(repo_name)
    except:
        org.create_repo(repo_name)
        repo = org.get_repo(repo_name)
        repo.create_file("placeholder", "Create placeholder", repo_name)
    
    try:
        release = repo.create_git_release(timestamp, filehash, filehash)
    except:
        releases = repo.get_releases()
        release = next((r for r in releases if r.tag_name == timestamp), None)

    try:
        release.upload_asset(filehash + ".zip")
        value = 1
    except:
    
    return value

def generateOTA():
    e = os.environ
    response = {}
    info['device'] = e.get('device')
    info['edition'] = e.get('edition')
    info['base'] = e.get('base')
    info['release'] = "official" if e.get('test_branch') != 'yes' and e.get('variant') != 'eng' else "unofficial"
    info['filename'] = runShAndReturnStdout("cat build.prop | sed -n -e 's/^.*ro.pixys.version=//p'") + '.zip'
    info['filehash'] = runShAndReturnStdout("md5sum " + info['filename'] + " | cut -d ' ' -f 1")
    info['filesize'] = runShAndReturnStdout("cat " + info['filename'] + " | wc -c")
    info['filepath'] = info['device'] + '/' + info['base'] + '/' + info['edition']
    info['version'] = runShAndReturnStdout("cat build.prop | sed -n -e 's/^.*ro.modversion=//p'")
    info['timestamp'] = runShAndReturnStdout("cat build.prop | sed -n -e 's/^.*ro.pixys.build.date=//p'")
    
    return response

def sendBuild():
    resp = generateOTA()
    response = buildUpload(resp)
    
    if not response:
        pass
