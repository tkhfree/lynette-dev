from lark import Lark, Tree, Token

import json,os

def execute(output_parameter):
    print("output...")

    topo = {}
    with open(output_parameter["sys_path"] + "//component//topo//topo.json",'r') as file:
        topo = json.load(file)
    relation_node_frag = {}
    for node in topo:
        relation_node_frag[node] = []

    read_dir = output_parameter["sys_path"] + "//component//code//"
    write_dir = output_parameter["output_path"]

    # 获取该文件夹下的所有文件名列表
    file_list = os.listdir(write_dir) 
    # 遍历文件列表并删除每个文件
    for file in file_list:
        # 构建完整的文件路径
        file_path = os.path.join(write_dir, file)      
        if os.path.isfile(file_path):
            # 如果是文件则直接删除
            os.remove(file_path)

    for node in topo:
        file_control = node + "_control"
        file_deparser = node + "_deparser"
        file_parser  = node + "_parser"
        file_entry   = node + "_entry"
        file_header  = node + "_header"
        with open(write_dir + node + ".p4","w") as f_w:
            #头文件
            if 1==1 :
                f_w.write("#include <core.p4>\n")
                if topo[node]["resource"] == "CPU":
                    f_w.write("#include <v1model.p4>\n\n")
                elif topo[node]["resource"] == "ASIC":
                    f_w.write("#include <tna.p4>\n\n")
                else:
                    print("error-lynette-output-what resource 78451")
                    exit()

            #header
            if 1 == 1:
                with open(read_dir + file_header, "r") as f_r:
                    line = f_r.readline()
                    while line :
                        f_w.write(line)
                        line = f_r.readline()
                f_w.write("\n")

            #parser
            if 1 == 1:
                if topo[node]["resource"] == "CPU":
                    f_w.write("parser LynetteParser(packet_in pkt, out ")
                    f_w.write(output_parameter["header_name"])
                    f_w.write(" hdr, inout global_metadata_t gmeta, inout standard_metadata_t im)")
                elif topo[node]["resource"] == "ASIC":
                    f_w.write("parser LynetteIngressParser(packet_in pkt,out ")
                    f_w.write(output_parameter["header_name"])
                    f_w.write(" hdr,out global_metadata_t meta,out ingress_intrinsic_metadata_t ig_intr_md)")
                else:
                    print("error-lynette-output-what resource 78451")
                    exit()
                f_w.write("{\n")
                with open(read_dir + file_parser, "r") as f_r:
                    line = f_r.readline()
                    while line :
                        if topo[node]["resource"] == "ASIC":
                            line = line.replace("transition parse_ethernet;",
                                                 "pkt.extract(ig_intr_md);\n        pkt.advance(PORT_METADATA_SIZE);\n        transition parse_ethernet;")
                        f_w.write(line)
                        line = f_r.readline()
                f_w.write("}\n")
                f_w.write("\n")

            #v1mod的checksum
            if 1 == 1:
                if topo[node]["resource"] == "CPU":
                    f_w.write("control LynetteVerifyChecksum(inout ")
                    f_w.write(output_parameter["header_name"])
                    f_w.write(" hdr, inout global_metadata_t gmeta) {\n")
                    f_w.write("    apply {  }\n")
                    f_w.write("}\n")
                    f_w.write("\n")

            #ingress
            if 1 == 1:
                with open(read_dir + file_control, "r") as f_r:
                    line = f_r.readline()
                    if topo[node]["resource"] == "CPU":
                        f_w.write("control LynetteIngress(\n")
                        f_w.write("    inout ")
                        f_w.write(output_parameter["header_name"])
                        f_w.write(" hdr,\n")
                        f_w.write("    inout global_metadata_t gmeta,\n")
                        f_w.write("    inout standard_metadata_t im)\n")
                    elif topo[node]["resource"] == "ASIC":
                        f_w.write("control LynetteIngress(\n")
                        f_w.write("    inout ")
                        f_w.write(output_parameter["header_name"])
                        f_w.write(" hdr,\n")
                        f_w.write("    inout global_metadata_t gmeta,\n")
                        f_w.write("    in    ingress_intrinsic_metadata_t              ig_intr_md,\n")
                        f_w.write("    in    ingress_intrinsic_metadata_from_parser_t  ig_prsr_md,\n")
                        f_w.write("    inout ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md,\n")
                        f_w.write("    inout ingress_intrinsic_metadata_for_tm_t       ig_tm_md)\n")
                    else:
                        print("error-lynette-output-what resource 78451")
                        exit()
                    f_w.write("{\n")
                    while line:
                        f_w.write("    ")
                        if topo[node]["resource"] == "CPU":
                            if "LynettePKT" in line:
                                line = line.replace("LynettePKT","im")
                            if "LynetteDrop" in line:
                                line = line.replace("LynetteDrop","mark_to_drop(im)")
                            if "LynetteHeaderCompress" in line:
                                line = line.replace("LynetteHeaderCompress","header_compress")
                            if "LynetteOutPort" in line:
                                line = line.replace("LynetteOutPort","egress_spec")
                            if "LynetteInPort" in line:
                                line = line.replace("LynetteInPort","ingress_port")
                        elif topo[node]["resource"] == "ASIC":
                            if "LynettePKT.LynetteOutPort" in line:
                                line = line.replace("LynettePKT.LynetteOutPort","ig_tm_md.ucast_egress_port")
                            if "LynetteDrop" in line:
                                line = line.replace("LynetteDrop","ig_dprsr_md.drop_ctl = 1")
                            if "LynettePKT.LynetteInPort" in line:
                                line = line.replace("LynettePKT.LynetteInPort","ig_intr_md.ingress_port")
                        else:
                            print("error-lynette-output-what resource 78451")
                            exit()
                        f_w.write(line)
                        line = f_r.readline()
                    f_w.write("}\n")
                f_w.write("\n")

            #deparser
            if 1 == 1:
                with open(read_dir + file_deparser, "r") as f_r:
                    if topo[node]["resource"] == "CPU":
                        f_w.write("control LynetteDeparser(packet_out pkt, in ")
                        f_w.write(output_parameter["header_name"])
                        f_w.write(" hdr) {\n")
                    elif topo[node]["resource"] == "ASIC":
                        f_w.write("control LynetteIngressDeparser(packet_out pkt,inout ")
                        f_w.write(output_parameter["header_name"])
                        f_w.write(" hdr,in global_metadata_t meta,in ingress_intrinsic_metadata_for_deparser_t ig_dprsr_md){\n")
                    else:
                        print("error-lynette-output-what resource 78451")
                        exit()
                    line = f_r.readline()
                    while line :
                        f_w.write(line)
                        line = f_r.readline()
                    f_w.write("}\n")
                f_w.write("\n")

            #rest
            if 1 == 1:
                if topo[node]["resource"] == "CPU":
                    with open(output_parameter["sys_path"] + "//component//rest//rest_v1mod", "r") as f_r:
                        line = f_r.readline()
                        while line :
                            line = line.replace("LynetteHeader",output_parameter["header_name"])
                            f_w.write(line)
                            line = f_r.readline()
                elif topo[node]["resource"] == "ASIC":
                    with open(output_parameter["sys_path"] + "//component//rest//rest_tna", "r") as f_r:
                        line = f_r.readline()
                        while line :
                            line = line.replace("LynetteHeader",output_parameter["header_name"])
                            f_w.write(line)
                            line = f_r.readline()
                else:
                    print("error-lynette-output-what resource 78451")
                    exit()
        with open(read_dir + file_entry) as f_r:
            json_t = json.load(f_r)
            if topo[node]["resource"] == "CPU":
                json_file_to_w = write_dir + node + "_entry.json"
            elif topo[node]["resource"] == "ASIC":
                json_file_to_w = write_dir + node + "_entry.py"
            with open(json_file_to_w,"w") as f_w:
                if topo[node]["resource"] == "CPU":
                    json.dump(json_t,f_w,indent=2)
                elif topo[node]["resource"] == "ASIC":
                    for entry in json_t["entries"]:
                        #print("out put 55",entry)
                        f_w.write("bfrt." + node + ".pipe.LynetteIngress.")
                        f_w.write(entry['table'])
                        f_w.write(".add_with_")
                        f_w.write(entry['action_name'])
                        f_w.write("(")
                        douhao = 0
                        for key in entry['match']:
                            if douhao == 0:
                                douhao = douhao + 1
                            else:
                                f_w.write(", ")
                            key_v = entry['match'][key][0]
                            if "." in key_v:
                                key_v = "\"" + key_v + "\""
                            if ":" in key_v:
                                key_vt = key_v.split(":")
                                key_v = "0x" + key_vt[0]
                                i = 1
                                while i < len(key_vt):
                                    for v in range(4-len(key_vt[i])):
                                        key_v = key_v + "0"
                                    key_v = key_v + key_vt[i]
                                    i = i + 1
                            if "." in key:
                                key_m = key.split(".")
                                key_m = key_m[-1]
                            else:
                                key_m = key
                            f_w.write(key_m)
                            f_w.write(" = ")
                            f_w.write(key_v)
                        int_v = 0
                        for value in entry['action_params']:
                            f_w.write(", ")
                            value_m = "value_" + str(int_v)
                            value_v = entry['action_params'][value][0]
                            f_w.write(value_m)
                            f_w.write(" = ")
                            f_w.write(value_v)
                            int_v = int_v + 1
                        f_w.write(")\n")
                
    

    return topo
            

            
