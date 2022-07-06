from django.shortcuts import render
from django.views.generic import View
from rest_framework.decorators import api_view, renderer_classes
from django.http import HttpResponse
import jenkins
import datetime
import math
import random
import json

server = jenkins.Jenkins(
    "host",
    username="usrnm",
    password="pswd",
)


@api_view(("GET",))
def get_console_output(req):
    req_data = req.GET["data"].split(":::")
    data = str(server.get_build_console_output(req_data[0], int(req_data[1]))).split(
        "\n"
    )
    data = {"console_output": data, "build_no": req_data[1]}
    return HttpResponse(
        json.dumps({"data": data, "success": True}), content_type="application/json"
    )


def get_selected_branch():
    jobs = server.get_jobs()
    select_branch = []
    for i in jobs:
        if i["name"] == "assetmanagement":
            data = server.get_job_info(i["name"])
            if "jobs" in data.keys():
                for j in data["jobs"]:
                    val = i["name"] + "/" + j["name"]
                    select_branch.append({"val": val, "des": j["name"].replace('%2','_')})

    return select_branch


def get_builds_information(branch, *a, **b):
    lst = []
    build_table = []
    branch = branch if branch else "assetmanagement/UT_90_New_TestCases"
    info = server.get_job_info(branch)
    select_branch = get_selected_branch()
    builds = info["builds"]

    suc, fai, uns, abo = (0, 0, 0, 0)
    build_runners = []
    for i in range(0, len(builds)):
        lst.append(builds[i]["number"])
        build_info = server.get_build_info(branch, builds[i]["number"])
        build_table.append(build_info)
        if build_info["result"] == "FAILURE":
            fai = fai + 1
        elif build_info["result"] == "SUCCESS":
            suc = suc + 1
        elif build_info["result"] == "UNSTABLE":
            uns = uns + 1
        else:
            abo = abo + 1
        if "causes" in build_info["actions"][0].keys():
            if "userName" in build_info["actions"][0]["causes"][0].keys():
                build_runners.append(build_info["actions"][0]["causes"][0]["userName"])
                continue
        build_runners.append("Auto Build")

    build_runners_data = []
    for i in list(set(build_runners)):
        letters = "0123456789ABCDEF"
        color = "#"
        for j in range(0, 6):
            color = color + letters[math.floor(random.random() * 16)]
        build_runners_data.append([i.capitalize(), build_runners.count(i), color])
    build_runners_data = sorted(build_runners_data, key=lambda i: i[1], reverse=True)
    build_runners_data.insert(0, ["Task", "Build Runner Chart", {"role": "style"}])

    data = {
        "build_table": build_table,
        "build_status_pie_data": [suc, fai, uns, abo],
        "build_numbers": lst,
        "build_runners_bar_data": build_runners_data,
        "branch": branch,
        "select_branch": select_branch,
    }
    return data


def builds_table(data, branch):
    tim_lst, build_no_lst = ["Time(Min)"], ["Build"]
    for i in range(0, len(data)):
        tim = round((data[i]["duration"] / 1000) / 60, 1)

        tim_lst.append(int(tim))
        build_no_lst.append(data[i]["number"])
        timestamp = int(str(data[i]["timestamp"])[:10])
        timestamp = datetime.datetime.fromtimestamp(timestamp)
        time = timestamp.strftime("%Y-%m-%d %H:%M")
        commit = data[i]["description"] if data[i]["description"] != None else "N/A"

        data[i] = {
            "s_no": i + 1,
            "build_no": str(data[i]["id"]),
            "branch": data[i]["fullDisplayName"],
            "path": str(branch),
            "result": data[i]["result"],
            "description": commit,
            "date": time,
            "duration": str(round(tim / 60, 1)) + "H" if tim > 60 else str(tim) + "M",
        }
    tim_duration_graph_data = json.loads(json.dumps(list(zip(build_no_lst, tim_lst))))
    return data, tim_duration_graph_data[:50]


def generate_dashboard_data(request):
    branch = request.GET.dict()["branch"] if request.GET else False
    data = get_builds_information(branch)
    build_table_data, tim_duration_graph_data = builds_table(data["build_table"], data["branch"])
    labels, build_status_pie_data, build_runners_bar_data = (
        data["build_numbers"],
        data["build_status_pie_data"],
        data["build_runners_bar_data"],
    )
    select_branch = data["select_branch"]

    chart_label = "success-failure rate "
    status = ["Success", "Failure", "Unstable", "Abort"]
    colours = ["green", "red", "orange", "blue"]

    pie_data = list(zip(status, build_status_pie_data))
    pie_data.insert(0, ["Task", "Build Status Chart"])

    builds = list(
        map(
            lambda x: {"des": x[0], "count": x[1], "colour": x[2]},
            list(zip(status, build_status_pie_data, colours)),
        )
    )
    builds.insert(0, {"des": "Jobs", "count": sum(build_status_pie_data), "colour": "grey"})

    data = {
        "labels": labels,
        "chartLabel": chart_label,
        "chartdata": build_status_pie_data,
        "pie": pie_data,
        "bar": build_runners_bar_data,
        "bg_colours": colours,
        "tim_plot": tim_duration_graph_data,
    }
    return data, build_table_data, select_branch, builds


class HomeView(View):
    def get(self, request):
        # try:
        data, build_table_data, select_branch, builds = generate_dashboard_data(
            request
        )
        return render(
            request,
            "index.html",
            {
                "builds_table": build_table_data,
                "data": json.dumps(data),
                "select_branch": select_branch,
                "builds": builds,
            },
        )

class LayoutView(View):
    def get(self,request):
        return render(request,"Anypage.html")