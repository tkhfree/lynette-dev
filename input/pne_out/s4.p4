#include <core.p4>
#include <v1model.p4>

header ethernet_t {
    bit<48> dmac;
    bit<48> smac;
}
header eth_type_t {
    bit<16> value;
}
header geo_t {
    bit<4> version;
    bit<4> nh_basic;
    bit<8> reserved_basic;
    bit<8> lt;
    bit<8> rhl;
    bit<4> nh_common;
    bit<4> reserved_common_a;
    bit<4> ht;
    bit<4> hst;
    bit<8> tc;
    bit<8> flag;
    bit<16> pl;
    bit<8> mhl;
    bit<8> reserved_common_b;
}
header gbc_t {
    bit<16> sn;
    bit<16> reserved_gbc_a;
    bit<64> gnaddr;
    bit<32> tst;
    bit<32> lat;
    bit<32> longg;
    bit<1> pai;
    bit<15> s;
    bit<16> h;
    bit<32> geoAreaPosLat;
    bit<32> geoAreaPosLon;
    bit<16> disa;
    bit<16> disb;
    bit<16> angle;
    bit<16> reserved_gbc_b;
}
header mf_guid_t {
    bit<32> mf_type;
    bit<32> src_guid;
    bit<32> dest_guid;
}

struct header_t {
    ethernet_t ethernet;
    eth_type_t eth_type;
    geo_t geo;
    gbc_t gbc;
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
            0x8947: parse_geo;
            0x27C0: parse_mf;
            default: accept;
        }
    }
    state parse_geo {
        pkt.extract(hdr.geo);
        transition select(hdr.geo.ht) {
            0x0004: parse_gbc;
            default: accept;
        }
    }
    state parse_gbc {
        pkt.extract(hdr.gbc);
        transition accept;
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
    
    action Alice_geo_Router_Forwarding_Geo_geoHostTable_action(bit<9> value_0)
    {
        im.egress_spec = value_0;
    }
    action Alice_geo_Router_Forwarding_Geo_geoHostTable_action_1()
    {
        mark_to_drop(im);
    }
    action Bob_mf_Router_Forwarding_Mf_mfHostTable_action(bit<9> value_0)
    {
        im.egress_spec = value_0;
    }
    action Bob_mf_Router_Forwarding_Mf_mfHostTable_action_1()
    {
        mark_to_drop(im);
    }
    
    table Alice_geo_Router_Forwarding_Geo_geoHostTable{
        key = {
            hdr.gbc.geoAreaPosLat : exact;
        }
        actions = {
            Alice_geo_Router_Forwarding_Geo_geoHostTable_action;
            Alice_geo_Router_Forwarding_Geo_geoHostTable_action_1;
        }
        default_action = Alice_geo_Router_Forwarding_Geo_geoHostTable_action_1();
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
    
        if(hdr.geo.isValid())
        {
            Alice_geo_Router_Forwarding_Geo_geoHostTable.apply();
        }
    
        /*******************************************/
    
    
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
        pkt.emit(hdr.geo);
        pkt.emit(hdr.gbc);
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