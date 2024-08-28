Obsoleted test cases: testset_story279464.py test case.
Description:
    Creating a 'vm-firewall-rule' item, then creating the plan,
    will result in a 'DoNothingPlanError'.
Reason why obsoleted:
    Story was a modelling story which enabled TORF-279479. As
    TORF-279479 has been finished, TORF-279464 is now obsolete & a plan
    will be created rather than a 'DoNothingPlanError'.
Gerrit review to obsolete test case(s): https://gerrit.ericsson.se/#/c/4058949/
TMS ID: torf_279464_tc_13