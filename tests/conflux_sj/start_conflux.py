import subprocess
import time
import re
import os
import threading

# ~/conflux-rust/tests/conflux_sj$ python3 start_conflux.py 
def do_experiment():
    command = "nohup /home/shijing/python3.10_dir/bin/python3.10 /home/shijing/conflux_master/conflux-rust/tests/sign_test.py >> output.txt 2>&1 &"
    subprocess.run(command, shell=True)
    

def get_tmpdir(path_head):
    with open(path_head + "file.txt", "r") as file:
        tmpdir = file.readline()[:-1]
    return tmpdir

def get_client():
    with open("file.txt", "r") as file:
        lines = file.readlines()
    
        sign_times = []
        for line in lines:
            line = line.strip()
            index = line.find("【performance】sign:")
            if index != -1:
                sign_time = line[index + len("【performance】sign:"):]
                sign_times.append(int(sign_time))

        return sum(sign_times) / len(sign_times)
    
def get_node_metrics(tmpdir, node):
    parsed_data = {}
    with open(tmpdir + "/node"+ str(node) +"/metrics.log", "r") as file:
        lines = file.readlines()
    for line in lines:
        if "performance testing" in line:
            data_start_index = line.find("{")
            data_end_index = line.find("}")
            if data_start_index != -1 and data_end_index != -1:
                line = line[data_start_index + 1: data_end_index]
                items = line.split(", ")
                for item in items:
                    key, value = item.split(": ")
                    if "mean" in key:
                        parsed_data[key.strip()[:key.find(".")]] = float(value.strip())
    return parsed_data


def get_broadcast(tmpdir):
    parsed_data = {}
    with open(tmpdir + "/node1/conflux.log", "r") as file:
        lines = file.readlines()
    for line in lines:
        if "[performance testing] block hash:" in line:
            block_hash = re.search(r"hash:0x([0-9a-fA-F]+)", line).group()[len("hash:"):]
            timestamp = re.search(r"timestamp:([0-9]+)", line).group()[len("timestamp:"):]
            parsed_data[block_hash] = timestamp

    with open(tmpdir + "/node0/conflux.log", "r") as file:
        lines = file.readlines()
    for line in lines:
        if "[performance testing] receive block hash:" in line:
            block_hash = re.search(r"hash:0x([0-9a-fA-F]+)", line).group()[len("hash:"):]
            timestamp = re.search(r"timestamp:([0-9a-fA-F]+)", line).group()[len("timestamp:"):]
            # print(block_hash + " " + timestamp)

            if parsed_data.get(block_hash) is not None:
                parsed_data[block_hash] = abs(int(parsed_data[block_hash]) - int(timestamp))
    
    values = parsed_data.values()
    average = sum(values) / len(values)
    return average

# [performance testing] Waiting

def get_waiting(tmpdir):
    parsed_data = {}
    with open(tmpdir + "/node0/conflux.log", "r") as file:
        lines = file.readlines()
    for line in lines:
        if "[performance testing] Waiting start." in line:
            blockhash = re.search(r"hash:0x([0-9a-fA-F]+)", line).group()[len("hash:"):]
            timestamp = re.search(r"timestamp:([0-9a-fA-F]+)", line).group()[len("timestamp:"):]
            parsed_data[blockhash] = timestamp
    
    for line in lines:
        if "[performance testing] Waiting finished." in line:
            blockhash = re.search(r"hash:0x([0-9a-fA-F]+)", line).group()[len("hash:"):]
            timestamp = re.search(r"timestamp:([0-9a-fA-F]+)", line).group()[len("timestamp:"):]
            if parsed_data.get(blockhash) is not None:
                parsed_data[blockhash] = abs(int(timestamp) - int(parsed_data[blockhash]))

    values = parsed_data.values()
    average = sum(values) / len(values)
    return average
          

def get_metrics(tmpdir):
    miner_data = get_node_metrics(tmpdir, 1) # miner
    other_data = get_node_metrics(tmpdir, 0)

    for key, value in other_data.items():
        if miner_data.get(key) is None:
            miner_data[key] = value
    
    sign_time = get_client()
    miner_data["sign"] = sign_time

    avg_broadcast_time = get_broadcast(tmpdir)
    miner_data["broadcast"] = avg_broadcast_time

    avg_waiting_time = get_waiting(tmpdir)
    miner_data["waiting"] = avg_waiting_time
    
    print(miner_data)



def is_exeriment_filished():
    while True:
        if os.path.exists("output.txt") == False:
            continue
        with open("output.txt", "r", encoding='utf-8') as file:
            content = file.read()
            if "Stopping nodes" in content:
                return 
            else:
                time.sleep(5)

def get_remote_broadcast_time(ips):
    block_map = {}
    for ip in ips:
        with open("./block_" + ip.replace(".", "_") + ".log") as file:
            lines = file.readlines()
            for line in lines:
                if "mining" in line:
                    block_hash_pattern = r"block hash:(0x\w+)"
                    block_hash_matches = re.findall(block_hash_pattern, line)

                    time_pattern = r"timestamp:(\d+)"
                    time_matches = re.findall(time_pattern, line)
                    if time_matches and block_hash_matches != 0 :
                        timestamp = time_matches[0]
                        block_hash = block_hash_matches[0]

                        block_map[block_hash] = [int(timestamp)]

    # get receive time
    for ip in ips:
        with open("./block_" + ip.replace(".", "_") + ".log") as file:
            lines = file.readlines()
            for line in lines:
                block_hash_pattern = r'receive block hash:(0x\w+)'
                block_hash_matches = re.findall(block_hash_pattern, line)

                if len(block_hash_matches) == 0:
                    continue

                for block_item in block_map:
                    if block_item[0] in line:
                        time_pattern = r'timestamp:(\d+)'
                        time_matches = re.findall(time_pattern, line)
                        if time_matches:
                            block_map[block_hash_matches[0]].append(int(time_matches[0]))
                            break
    sum = 0
    for _, value in block_map.items():
        sum = sum + (max(value) - min(value))
    
    print("broadcast time:", sum/len(block_map))
    return block_map

def get_blockid(line):
    block_hash_pattern = r"block hash:(0x\w+)"
    block_hash_matches = re.findall(block_hash_pattern, line)
    if block_hash_matches:
        return block_hash_matches[0]
    else:
        return ""

def get_timestamp(line):
    time_pattern = r"timestamp:(\d+)"
    time_matches = re.findall(time_pattern, line)
    if time_matches:
        return int(time_matches[0])
    else:
        return 0

def block_id_in_list(block_id, blocks):
    for block in blocks:
        if block == block_id:
            return True
        else:
            return False

def get_remote_wait_time(ips, blocks):
    avg_time_per_ips = []
    for ip in ips:
        wait_time_per_ips = {}

        with open("./block_" + ip.replace(".", "_") + ".log") as file:
            lines = file.readlines()
            for line in lines:
                if "Waiting start. " in line:
                    block_id = get_blockid(line)
                    if block_id_in_list(block_id, blocks) and get_timestamp(line) != 0:
                        wait_time_per_ips[block_id] = get_timestamp(line)
                    
                if "Waiting finished." in line:
                    block_id = get_blockid(line) 
                    if block_id_in_list(block_id, blocks) and get_timestamp(line) !=0 :
                        wait_time_per_ips[block_id] = get_timestamp(line) - wait_time_per_ips[block_id]
        
        avg_time_per_ips.append(sum(wait_time_per_ips.values())/len(wait_time_per_ips.values())) 
    
    print("wait time:", sum(avg_time_per_ips)/len(avg_time_per_ips))
    return sum(avg_time_per_ips)/len(avg_time_per_ips)

def get_remote_metrics():
    ips = []

    # get remote log
    with open("../extra-test-toolkits/scripts/ips") as file:
        lines = file.readlines()
        for line in lines:
            ip = line.strip()
            ips.append(ip)

    for ip in ips:
        cmd = "scp -r ubuntu@" + ip + ":/home/ubuntu/block.log ./block_" + ip.replace(".", "_") + ".log"
        ret = os.system(cmd)

    # get broadcast time
    block_map = get_remote_broadcast_time(ips)

    # get wait time
    blocks = block_map.keys()
    get_remote_wait_time(ips, blocks)
    



# def write_excel():

def delete_file():
    if os.path.exists("output.txt"):
        os.remove("output.txt")
    if os.path.exists("file.txt"):
        os.remove("file.txt")
    
if __name__ == "__main__":
    action = input("Enter action (experiment(e)/metrics(m)): ")
    if action == "e":
        delete_file()
        do_experiment()
    elif action == "m":
        tmpdir = get_tmpdir("")
        get_metrics(tmpdir)
    elif action == "rm":
        get_remote_metrics()



    # write_excel()



