#include <core.p4>
#include <v1model.p4>

header ethernet_t {
    bit<48> dmac;
    bit<48> smac;
}
header eth_type_t {
    bit<16> value;
}
header mf_guid_t {
    bit<32> mf_type;
    bit<32> src_guid;
    bit<32> dest_guid;
}

struct header_t {
    ethernet_t ethernet;
    eth_type_t eth_type;
    mf_guid_t mf;
}
struct global_metadata_t {
}

parser LynetteParser(packet_in pkt, out header_t hdr, inout global_metadata_t gmeta, inout standard_metadata_t im){
    state start {
        transition parse_ethernet;
    }
    state parse_ethernet {
        pkt.extract(hdr.ethernet);
        transition parse_eth_type;
    }
    state parse_eth_type {
        pkt.extract(hdr.eth_type);
        transition select(hdr.eth_type.value) {
            0x27C0: parse_mf;
            default: accept;
        }
    }
    state parse_mf {
        pkt.extract(hdr.mf);
        transition accept;
    }
}

control LynetteVerifyChecksum(inout header_t hdr, inout global_metadata_t gmeta) {
    apply {  }
}

control LynetteIngress(
    inout header_t hdr,
    inout global_metadata_t gmeta,
    inout standard_metadata_t im)
{
    
    action Bob_mf_Router_Forwarding_Mf_mfHostTable_action(bit<9> value_0)
    {
        im.egress_spec = value_0;
    }
    action Bob_mf_Router_Forwarding_Mf_mfHostTable_action_1()
    {
        mark_to_drop(im);
    }
    
    table Bob_mf_Router_Forwarding_Mf_mfHostTable{
        key = {
            hdr.mf.dest_guid : exact;
        }
        actions = {
            Bob_mf_Router_Forwarding_Mf_mfHostTable_action;
            Bob_mf_Router_Forwarding_Mf_mfHostTable_action_1;
        }
        default_action = Bob_mf_Router_Forwarding_Mf_mfHostTable_action_1();
    }
    
    
    apply {
    
        /*******************************************/
    
        if(hdr.mf.isValid())
        {
            Bob_mf_Router_Forwarding_Mf_mfHostTable.apply();
        }
    
        /*******************************************/
    
    
        /*******************************************/
    
    }
}

control LynetteDeparser(packet_out pkt, in header_t hdr) {
    apply{ 
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.eth_type);
        pkt.emit(hdr.mf);
    } 
}

control LynetteEgress(
    inout header_t                          hdr,
    inout global_metadata_t                         gmeta,
    inout standard_metadata_t standard_metadata)
{
    apply {
    }
}

control LynetteComputeChecksum(inout header_t  hdr, inout global_metadata_t gmeta) {
        apply {
    }
}

V1Switch(
    LynetteParser(),
    LynetteVerifyChecksum(),
    LynetteIngress(),
    LynetteEgress(),
    LynetteComputeChecksum(),
    LynetteDeparser()
)main;