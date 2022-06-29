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
    "https://testmap-deploy.adfdata.net",
    username="manavalladilipkumar",
    password="Dilip@2129",
)


@api_view(('GET',))
def get_console_output(req):
    req_data=req.GET['data'].split(':::')
    data=str(server.get_build_console_output(req_data[0], int(req_data[1]))).split('\n')
    data={'console_output':data,'build_no':req_data[1]}
    return HttpResponse(json.dumps({'data': data,'success':True}), content_type="application/json")

def get_builds_information(purpose):
    lst = []
    branch="assetmanagement/UT_90_New_TestCases"
    info = server.get_job_info(branch)
    builds = info["builds"]
    s = []
    if purpose == "graph":
        suc, fai, uns, abo = (0, 0, 0, 0)
        build_runners=[]
        for i in range(0,len(builds)):
            lst.append(builds[i]["number"])
            build_info = server.get_build_info(
                "assetmanagement/UT_90_New_TestCases", builds[i]["number"]
            )
            if build_info["result"] == "FAILURE":
                fai=fai+1
            elif build_info["result"] == "SUCCESS":
                suc=suc+1
            elif build_info["result"] == "UNSTABLE":
                uns= uns + 1
            else:
                abo=abo+1
            if 'causes' in build_info['actions'][0].keys():
                if 'userName' in build_info['actions'][0]['causes'][0].keys():
                    build_runners.append(build_info['actions'][0]['causes'][0]['userName'])
                    continue
            build_runners.append('Auto Build')
        build_runners_data=[]
        for i in list(set(build_runners)):
            letters = '0123456789ABCDEF'
            color = '#'
            for j in range(0, 6):
                color = color + letters[math.floor(random.random() * 16)]
            build_runners_data.append([i.capitalize(), build_runners.count(i), color])
        build_runners_data=sorted(build_runners_data, key = lambda i: i[1],reverse=True)
        build_runners_data.insert(0,['Task','Build Runner Chart',{ 'role': "style" }])
        return lst, [suc,fai,uns,abo],build_runners_data

    if purpose == "builds_table":
        for build in builds:
            build_info = server.get_build_info(
                branch, build["number"]
            )
            lst.append(build_info)
        return lst,branch
    return lst, s


def builds_table(request):
    data, branch = get_builds_information("builds_table")
    for i in range(0, len(data)):
        tim=round((data[i]["duration"]/60)/60,1)
        timestamp=int(str(data[i]['timestamp'])[:10])
        timestamp = datetime.datetime.fromtimestamp(timestamp)
        time=timestamp.strftime('%Y-%m-%d %H:%M')
        commit=data[i]["description"] if data[i]["description"]!=None else 'N/A'

        data[i] = {
            "s_no": i + 1,
            "build_no": str(data[i]["id"]),
            "branch": data[i]["fullDisplayName"],
            "path":str(branch),
            "result": data[i]["result"],
            "description": commit,
            "date":time,
            "duration":str(round(tim/60,1))+'H'if tim>60 else str(tim)+'M'
        }
    return data


class HomeView(View):
    def get(self, request, *args, **kwargs):
        build_table_data=builds_table('req')
        chart_label = "success-failure rate "
        labels, chart_data, build_runner = get_builds_information("graph")
        temp = ['Success', 'Failure', 'Unstable', 'Abort']
        pie_data = list(map(lambda x: [temp[chart_data.index(x)], x], chart_data))
        temp = ['green', 'red', 'orange', 'blue']
        pie_data.insert(0, ['Task', 'Build Status Chart'])
        builds=list(map(lambda x:{'des':x[0],'count': x[1],'colour': temp[pie_data.index(x)-1]},pie_data[1:]))
        builds.insert(0,{'des':'Jobs','count': sum(i[1] for i in pie_data[1:]),'colour':'grey'})
        data = {
            "labels": labels,
            "chartLabel": chart_label,
            "chartdata": chart_data,
            "pie": pie_data,
            "bar": build_runner,
            "bg_colours": temp,
        }
        return render(request, "index.html", {"builds_table": build_table_data,"data":json.dumps(data),"builds":builds})
