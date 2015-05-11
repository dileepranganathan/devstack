#!/usr/bin/python

import sys
import logging
import os
import datetime
import string
from libs.gbp_conf_libs import Gbp_Config
from libs.gbp_verify_libs import Gbp_Verify
from libs.gbp_fab_traff_libs import Gbp_def_traff
from libs.gbp_pexp_traff_libs import Gbp_pexp_traff
from libs.raise_exceptions import *
from testsuites_setup_cleanup import super_hdr

class test_same_ptg_same_l2p_same_l3p(object):
    """
    This is a TestCase Class comprising
    all Datapath testcases for the Test Header:   
    same_ptg_same_l2p_same_l3p
    Every new testcases should be added as a new method in this class
    and call the testcase method inside the 'test_runner' method
    """
    # Initialize logging
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s - %(message)s', level=logging.WARNING)
    _log = logging.getLogger( __name__ )
    hdlr = logging.FileHandler('/tmp/testsuite_same_ptg_l2p_l3p.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    _log.addHandler(hdlr)
    _log.setLevel(logging.INFO)
    _log.setLevel(logging.DEBUG)

    def __init__(self,objs_uuid):

      self.gbpcfg = Gbp_Config()
      self.gbpverify = Gbp_Verify()
      self.gbpdeftraff = Gbp_def_traff()
      stack_name = super_hdr.stack_name
      heat_temp = super_hdr.heat_temp
      self.ntk_node = super_hdr.ntk_node
      self.ptg = objs_uuid['demo_same_ptg_l2p_l3p_ptg_id']
      self.test_2_prs = objs_uuid['demo_ruleset_norule_id']
      self.test_3_prs = objs_uuid['demo_ruleset_icmp_id']
      self.test_4_prs = objs_uuid['demo_ruleset_tcp_id']
      self.test_5_prs = objs_uuid['demo_ruleset_udp_id']
      self.test_6_prs = objs_uuid['demo_ruleset_icmp_tcp_id']
      self.test_7_prs = objs_uuid['demo_ruleset_icmp_udp_id']
      self.test_8_prs = objs_uuid['demo_ruleset_tcp_udp_id']
      self.test_9_prs = objs_uuid['demo_ruleset_all_id']

    def test_runner(self,log_string,location):
        """
        Method to run all testcases for this test_suite
        """
        #Note: Cleanup per testcases is not required,since every testcase updates the PTG, hence over-writing previous attr vals
        self.vm_loc = location
        test_list = [self.test_1_traff_with_no_prs,
                    self.test_2_traff_app_prs_no_rule,
                    self.test_3_traff_apply_prs_icmp,
                    self.test_4_traff_apply_prs_tcp,
                    self.test_5_traff_apply_prs_udp,
                    self.test_6_traff_apply_prs_icmp_tcp,
                    self.test_7_traff_apply_prs_icmp_udp,
                    self.test_8_traff_apply_prs_tcp_udp,
                    self.test_9_traff_apply_prs_all_proto,
                    self.test_10_traff_rem_prs
                    ]
                 
        for test in test_list:
            try:
               if test()!=1:
                  raise TestFailed("%s_%s_%s == FAILED" %(self.__class__.__name__.upper(),log_string.upper(),string.upper(test.__name__.lstrip('self.'))))
               else:
                  if 'test_1' in test.__name__ or 'test_2' in test.__name__:
                     self._log.info("%s_%s_%s 10 subtestcases == PASSED" %(self.__class__.__name__.upper(),log_string.upper(),string.upper(test.__name__.lstrip('self.'))))
                  else:
                     self._log.info("%s_%s_%s == PASSED" %(self.__class__.__name__.upper(),log_string.upper(),string.upper(test.__name__.lstrip('self.'))))
            except TestFailed as err:
               print err


    def verify_traff(self):
        """
        Verifies thes expected traffic result per testcase
        """
        #Incase of Same PTG all traffic is allowed irrespective what Policy-Ruleset is applied
        # Hence verify_traff will check for all protocols including the implicit ones
        gbpcfg = Gbp_Config()
        vm1_ip = gbpcfg.get_vm_subnet('VM1')[0]
        vm1_subn = gbpcfg.get_vm_subnet('VM1')[1]
        dhcp_ns = gbpcfg.get_netns(self.ntk_node,vm1_subn)
        if self.vm_loc == 'diff_host_same_leaf': 
           vm3_ip = gbpcfg.get_vm_subnet('VM3',ret='ip')
           print vm1_ip, vm1_subn, vm3_ip, dhcp_ns
           gbppexptraff = Gbp_pexp_traff(self.ntk_node,dhcp_ns,vm1_ip,vm3_ip)
        if self.vm_loc == 'same_host':
           vm2_ip = gbpcfg.get_vm_subnet('VM2',ret='ip')
           print vm1_ip, vm1_subn, vm2_ip, dhcp_ns
           gbppexptraff = Gbp_pexp_traff(self.ntk_node,dhcp_ns,vm1_ip,vm2_ip)
        results=gbppexptraff.test_run()
        print 'Results from the Testcase == ', results 
        failed={}
        failed = {key: val for key,val in results.iteritems() if val == 0}
        if len(failed) > 0:
            print 'Following traffic_types %s = FAILED' %(failed)
            return failed
        else:
            return 1

    def test_1_traff_with_no_prs(self):
        """
        Run traff test when PTG is with NO Contract
        """
        return self.verify_traff()

    def test_2_traff_app_prs_no_rule(self):
        """
        Update the in-use PTG with a PRS which has NO-Rule
        Send traff
        """
        prs = self.test_2_prs
        if self.gbpcfg.gbp_policy_cfg_all(2,'group',self.ptg,provided_policy_rule_sets="%s=scope" %(prs),consumed_policy_rule_sets="%s=scope" %(prs))!=0:
           return self.verify_traff()
        else:
           print 'Updating PTG = FAILED'
           return 0
 
    def test_3_traff_apply_prs_icmp(self):
        """
        Apply Policy-RuleSet to the in-use PTG
        Send traffic
        """
        prs = self.test_3_prs
        if self.gbpcfg.gbp_policy_cfg_all(2,'group',self.ptg,provided_policy_rule_sets="%s=scope" %(prs),consumed_policy_rule_sets="%s=scope" %(prs))!=0:
           return self.verify_traff()
        else:
           print 'Updating PTG == FAILED'
           return 0

    def test_4_traff_apply_prs_tcp(self):
        """
        Apply Policy-RuleSet to the in-use PTG
        Send traffic
        """
        prs = self.test_4_prs
        if self.gbpcfg.gbp_policy_cfg_all(2,'group',self.ptg,provided_policy_rule_sets="%s=scope" %(prs),consumed_policy_rule_sets="%s=scope" %(prs))!=0:
           return self.verify_traff()
        else:
           print 'Updating PTG = FAILED'
           return 0

    def test_5_traff_apply_prs_udp(self):
        """
        Apply Policy-RuleSet to the in-use PTG
        Send traffic
        """
        prs = self.test_5_prs
        if self.gbpcfg.gbp_policy_cfg_all(2,'group',self.ptg,provided_policy_rule_sets="%s=scope" %(prs),consumed_policy_rule_sets="%s=scope" %(prs))!=0:
           return self.verify_traff()
        else:
           return 0

    def test_6_traff_apply_prs_icmp_tcp(self):
        """
        Apply Policy-RuleSet to the in-use PTG
        Send traffic
        """
        prs = self.test_6_prs
        if self.gbpcfg.gbp_policy_cfg_all(2,'group',self.ptg,provided_policy_rule_sets="%s=scope" %(prs),consumed_policy_rule_sets="%s=scope" %(prs))!=0:
           return self.verify_traff()
        else:
           return 0

    def test_7_traff_apply_prs_icmp_udp(self):
        """
        Apply Policy-RuleSet to the in-use PTG
        Send traffic
        """
        prs = self.test_7_prs
        if self.gbpcfg.gbp_policy_cfg_all(2,'group',self.ptg,provided_policy_rule_sets="%s=scope" %(prs),consumed_policy_rule_sets="%s=scope" %(prs))!=0:
           return self.verify_traff()
        else:
           return 0

    def test_8_traff_apply_prs_tcp_udp(self):
        """
        Apply Policy-RuleSet to the in-use PTG
        Send traffic
        """
        prs = self.test_8_prs
        if self.gbpcfg.gbp_policy_cfg_all(2,'group',self.ptg,provided_policy_rule_sets="%s=scope" %(prs),consumed_policy_rule_sets="%s=scope" %(prs))!=0:
           return self.verify_traff()
        else:
           return 0

    def test_9_traff_apply_prs_all_proto(self):
        """
        Apply Policy-RuleSet to the in-use PTG
        Send traffic
        """
        prs = self.test_9_prs
        if self.gbpcfg.gbp_policy_cfg_all(2,'group',self.ptg,provided_policy_rule_sets="%s=scope" %(prs),consumed_policy_rule_sets="%s=scope" %(prs))!=0:
           return self.verify_traff()
        else:
           return 0

    def test_10_traff_rem_prs(self):
        """
        Remove the PRS/Contract from the PTG
        Test all traffic types
        """
        if self.gbpcfg.gbp_policy_cfg_all(2,'group',self.ptg,provided_policy_rule_sets="",consumed_policy_rule_sets="")!=0:
           return self.verify_traff()
        else:
           return 0
