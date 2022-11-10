import requests

# VARS

INSTANCE_1 = "" # Could be your external/main instance like "gitlab.com"
INSTANCE_2 = "" # Could be your internal/secondary/backup/replica instance like "gitlab.example.com"
PARENT_GROUP = "" # Root group ID
PARENT_GROUP_FULL_PATH = "" # Root group name
EXTERNAL_API_KEY = "" # API key from INSTANCE_1 
INTERNAL_API_KEY = "" # API key from INSTANCE_2
INTERNAL_MIRROR_API_KEY = "" # API key from INSTANCE_2 with <oauth:key> format
AUTHENTICATION = {"Authorization": "Bearer " + EXTERNAL_API_KEY}
AUTHENTICATION_INTERNAL = {"Authorization": "Bearer " + INTERNAL_API_KEY}

# LIST OF GROUP ID FROM INSTANCE_1

group_response = requests.get("https://" + INSTANCE_1 + "/api/v4/groups/" + PARENT_GROUP + "/descendant_groups?per_page=50", headers=AUTHENTICATION)
groups = group_response.json()
group_id = [{"id": PARENT_GROUP, "full_path": PARENT_GROUP_FULL_PATH}]
for group in groups:
    group_id.append({"id": str(group["id"]), "full_path": str(group["full_path"])})

# LIST OF PROJECTS ID FROM INSTANCE_1 

project_id = []
for group_index in group_id:
    project_response = requests.get("https://" + INSTANCE_1 + "/api/v4/groups/" + str(group_index["id"]) + "/projects?per_page=300", headers=AUTHENTICATION)
    projects = project_response.json()
    for project in projects:
        project_id.append({"id": str(project["id"]), "name": str(project["name"]), "group": str(group_index["full_path"]), "path": str(project["path"]), "namespace.full_path": str(project["namespace"]["full_path"]) })

# CLEAN ALL MIRRORS

for mirror_index in project_id:
    mirror_response = requests.get("https://" + INSTANCE_1 + "/api/v4/projects/" + str(mirror_index["id"]) + "/remote_mirrors", headers=AUTHENTICATION)
    mirrors = mirror_response.json()
    for mirror_response_index in mirrors:
        requests.delete("https://" + INSTANCE_1 + "/api/v4/projects/" + str(mirror_index["id"]) + "/remote_mirrors/" + str(mirror_response_index["id"]), headers=AUTHENTICATION)

# START CLONE REPOSITORIES FROM INSTANCE_1 >> INSTANCE_2

for gitlab_project_id in project_id:
    clone_response = requests.post("https://" + INSTANCE_2 + "/api/v4/projects/", data={"name": str(gitlab_project_id["name"])}, headers=AUTHENTICATION_INTERNAL ).json()
    clone_project_id = str(clone_response["id"])
    requests.put("https://" + INSTANCE_2 + "/api/v4/projects/" + clone_project_id + "/transfer?namespace=" + str(gitlab_project_id["namespace.full_path"]), headers=AUTHENTICATION_INTERNAL).json()

# START MIRRORING FROM INSTANCE_1 >> INSTANCE_2

for gitlab_project_id in project_id:
    requests.post("https://" + INSTANCE_1 + "/api/v4/projects/" + str(gitlab_project_id["id"]) + "/remote_mirrors", headers=AUTHENTICATION, data={"url":"https://" + INTERNAL_MIRROR_API_KEY + "@" + INSTANCE_2 + "/" + str(gitlab_project_id["group"]) + "/" + str(gitlab_project_id["path"]) + ".git", "enabled":"true"})
