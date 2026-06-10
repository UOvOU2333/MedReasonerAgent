"""Unit tests for kg.drg_loader — CN-DRG 2018 grouping logic."""
from __future__ import annotations

import pytest
from kg.drg_loader import (
    ADRG_TABLE,
    CC_SET,
    COMPLICATION_SUFFIX,
    MCC_SET,
    MDC_TABLE,
    MEDICAL_ADRG,
    check_complications,
    get_adrg,
    get_mdc,
    load_drg_graph,
    resolve_drg,
)


# =============================================================================
# get_mdc() tests
# =============================================================================

class TestGetMdc:
    @pytest.mark.parametrize("icd_code,expected_mdc", [
        # 神经系统
        ("G40.0", "MDCA"),
        ("G45.9", "MDCA"),
        ("G20", "MDCA"),
        # 眼
        ("H25.0", "MDCB"),
        ("H40.0", "MDCB"),
        ("H52.4", "MDCB"),
        # 耳、鼻、口、喉
        ("H60.0", "MDCC"),
        ("J32.0", "MDCC"),
        ("K00.0", "MDCC"),
        # 呼吸系统
        ("J18.9", "MDCE"),
        ("J44.0", "MDCE"),
        ("J96.0", "MDCE"),
        # 循环系统
        ("I21.3", "MDCF"),
        ("I50.1", "MDCF"),
        ("I10", "MDCF"),
        # 消化系统
        ("C15.9", "MDCG"),
        ("K21.0", "MDCG"),
        ("D12.6", "MDCG"),
        # 肝胆胰
        ("K70.4", "MDCH"),
        ("K80.2", "MDCH"),
        ("B16.9", "MDCH"),
        # 骨骼肌肉
        ("M54.5", "MDCI"),
        ("S72.0", "MDCI"),
        # 皮肤
        ("L40.0", "MDCJ"),
        # 内分泌
        ("E11.9", "MDCK"),
        ("E03.9", "MDCK"),
        # 肾脏泌尿
        ("N18.3", "MDCL"),
        ("N39.0", "MDCL"),
        # 男性生殖
        ("C61.0", "MDCM"),
        # 女性生殖
        ("C56.0", "MDCN"),
        ("N80.0", "MDCN"),
        # 妊娠分娩
        ("O80.0", "MDCO"),
        # 新生儿
        ("P07.3", "MDCP"),
        # 血液
        ("D64.9", "MDCQ"),
        # 肿瘤
        ("C34.1", "MDCR"),
        # 感染
        ("A41.9", "MDCS"),
        ("B18.2", "MDCS"),
        # 精神
        ("F32.9", "MDCT"),
        # 损伤中毒
        ("T81.0", "MDCV"),
        ("S42.0", "MDCV"),
        # 烧伤
        ("T20.0", "MDCW"),
        ("T25.0", "MDCW"),
        # 其他
        ("Z00.0", "MDCX"),
        # 多发伤
        ("R07.0", "MDCZ"),
        ("R10.0", "MDCZ"),
    ])
    def test_mdc_lookup_returns_correct_code(self, icd_code, expected_mdc):
        result = get_mdc(icd_code)
        assert result is not None
        assert result["mdc"] == expected_mdc

    def test_mdc_returns_name(self):
        result = get_mdc("I21.3")
        assert result is not None
        assert "mdc_name" in result
        assert "循环系统" in result["mdc_name"]

    @pytest.mark.parametrize("icd_code", [
        "I21.3",
        "E11.9",
        "G40.0",
    ])
    def test_mdc_uppercase_input(self, icd_code):
        result = get_mdc(icd_code.upper())
        assert result is not None

    def test_mdc_lowercase_input(self):
        result = get_mdc("i21.3")
        assert result is not None

    def test_mdc_with_whitespace(self):
        result = get_mdc("  I21.3  ")
        assert result is not None
        assert result["mdc"] == "MDCF"

    def test_mdc_trailing_x_stripped(self):
        """X in ICD-10 codes (broad categories) should be ignored."""
        result = get_mdc("I21.3XXX")
        assert result is not None

    def test_mdc_no_match_returns_none(self):
        result = get_mdc("0ZZ.999")  # numeric prefix never in MDC table
        assert result is None

    def test_mdc_empty_string_returns_none(self):
        result = get_mdc("")
        assert result is None

    def test_mdc_all_26_mdcs_covered(self):
        """Ensure all 26 MDC categories can be reached by at least one ICD code."""
        covered = set(v[0] for v in MDC_TABLE.values())
        expected = {"MDCA", "MDCB", "MDCC", "MDCE", "MDCF", "MDCG", "MDCH",
                    "MDCI", "MDCJ", "MDCK", "MDCL", "MDCM", "MDCN", "MDCO",
                    "MDCP", "MDCQ", "MDCR", "MDCS", "MDCT", "MDCV", "MDCW",
                    "MDCX", "MDCZ"}
        assert covered == expected, f"Missing MDCs: {expected - covered}"

    def test_mdc_prefix_priority_longer_over_shorter(self):
        """Longer prefix (K83) should match before shorter prefix (K)."""
        result_k83 = get_mdc("K83.0")  # 胆管疾病 → MDCH
        assert result_k83 is not None
        assert result_k83["mdc"] == "MDCH"


# =============================================================================
# get_adrg() tests
# =============================================================================

class TestGetAdrg:
    def test_cabg_maps_to_fm1(self):
        result = get_adrg("MDCF", ["36.1"])
        assert result is not None
        assert result["adrg"] == "FM1"
        assert result["type"] == "surgical"

    def test_pci_maps_to_fm2(self):
        result = get_adrg("MDCF", ["36.0"])
        assert result is not None
        assert result["adrg"] == "FM2"
        assert result["type"] == "surgical"

    def test_cardiac_valve_surgery(self):
        result = get_adrg("MDCF", ["35.2"])
        assert result is not None
        assert result["adrg"] == "FL1"

    def test_hip_replacement(self):
        result = get_adrg("MDCI", ["81.51"])
        assert result is not None
        assert result["adrg"] == "IC3"
        assert result["type"] == "surgical"

    def test_knee_replacement(self):
        result = get_adrg("MDCI", ["81.54"])
        assert result is not None
        assert result["adrg"] == "IC3"

    def test_appendectomy(self):
        result = get_adrg("MDCG", ["47.0"])
        assert result is not None
        assert result["adrg"] == "GD1"

    def test_colorectal_resection(self):
        result = get_adrg("MDCG", ["45.7"])
        assert result is not None
        assert result["adrg"] == "GB1"

    def test_femoral_fracture_surgery(self):
        result = get_adrg("MDCI", ["79.3"])
        assert result is not None
        assert result["adrg"] == "ID1"

    def test_spinal_fusion(self):
        result = get_adrg("MDCI", ["81.0"])
        assert result is not None
        assert result["adrg"] == "IC1"

    def test_thoracotomy(self):
        result = get_adrg("MDCE", ["34.02"])
        assert result is not None
        assert result["adrg"] == "EB1"

    def test_cholecystectomy_laparoscopic(self):
        result = get_adrg("MDCH", ["51.2"])
        assert result is not None
        assert result["adrg"] == "HC2"

    def test_cholecystectomy_open(self):
        result = get_adrg("MDCH", ["51.3"])
        assert result is not None
        assert result["adrg"] == "HC2"

    def test_cesarean_section(self):
        result = get_adrg("MDCO", ["74.1"])
        assert result is not None
        assert result["adrg"] == "OB1"

    def test_nephrectomy(self):
        """55.8 (肾囊肿手术) → LA8 surgical"""
        result = get_adrg("MDCL", ["55.8"])
        assert result is not None
        assert result["type"] == "surgical"
        assert result["adrg"] == "LA8"

    def test_medical_fallback_for_renal_mdcl(self):
        """MDCL|57.9 → 膀胱其他手术 → surgical"""
        result = get_adrg("MDCL", ["57.9"])
        assert result is not None
        assert result["type"] == "surgical"

    def test_medical_fallback_for_unknown_renal_proc(self):
        """MDCL without surgical ADRG → uses medical fallback"""
        result = get_adrg("MDCL", [])
        assert result is not None
        assert result["type"] == "medical"
        assert result["adrg"] == "LR1"

    def test_craniotomy(self):
        result = get_adrg("MDCA", ["01.2"])
        assert result is not None
        assert result["adrg"] == "BA1"

    def test_prostatectomy_turp(self):
        result = get_adrg("MDCM", ["60.4"])
        assert result is not None
        assert result["adrg"] == "MA2"

    def test_hysterectomy_abdominal(self):
        result = get_adrg("MDCN", ["66.7"])
        assert result is not None
        assert result["adrg"] == "NA11"

    def test_medical_fallback_circulatory(self):
        result = get_adrg("MDCF", [])
        assert result is not None
        assert result["type"] == "medical"
        assert result["adrg"] == "FR3"

    def test_medical_fallback_respiratory(self):
        result = get_adrg("MDCE", [])
        assert result is not None
        assert result["type"] == "medical"
        assert result["adrg"] == "ER3"

    def test_medical_fallback_all_mdcs_have_fallback(self):
        """Every MDC should have a medical ADRG fallback."""
        mdcs = [v[0] for v in MDC_TABLE.values()]
        for mdc in mdcs:
            result = get_adrg(mdc, [])
            assert result is not None, f"No medical fallback for {mdc}"

    def test_adrg_empty_proc_list_uses_medical_fallback(self):
        result = get_adrg("MDCF", [""])
        assert result is not None
        assert result["type"] == "medical"

    def test_surgical_takes_priority_over_medical_fallback(self):
        """When a surgical procedure matches, it should be used instead of medical fallback."""
        result = get_adrg("MDCF", ["36.0", "36.1"])  # PCI + CABG, first wins
        assert result is not None
        assert result["type"] == "surgical"
        assert result["adrg"] == "FM2"  # 36.0 has priority (listed first)

    def test_adrg_first_matching_proc_returns(self):
        """When multiple proc codes match, the first one in the list should win."""
        result = get_adrg("MDCF", ["35.2", "36.0", "36.1"])
        assert result is not None
        assert result["matched_proc"] == "35.2"

    def test_adrg_procedure_prefix_truncation(self):
        """Shorter prefix (e.g., 51.) should match after longer (e.g., 51.2)."""
        result = get_adrg("MDCH", ["51.0"])
        assert result is not None
        assert result["adrg"] == "HC1"


# =============================================================================
# check_complications() tests
# =============================================================================

class TestCheckComplications:
    def test_mcc_takes_priority_over_cc(self):
        result = check_complications(["I21.3", "E11.9"])
        assert result["level"] == "MCC"
        assert "I21.3" in result["matched_mcc"]
        assert "E11.9" in result["matched_cc"]

    def test_mcc_identified(self):
        result = check_complications(["I21.3", "I22.0", "N17.9"])
        assert result["level"] == "MCC"
        assert len(result["matched_mcc"]) >= 2

    def test_cc_identified(self):
        result = check_complications(["E11.9", "I10", "N18.3"])
        assert result["level"] == "CC"
        assert len(result["matched_cc"]) >= 2

    def test_none_when_no_complications(self):
        result = check_complications(["Z00.0", "R10.0"])
        assert result["level"] == "NONE"
        assert result["matched_mcc"] == []
        assert result["matched_cc"] == []

    def test_empty_list_returns_none(self):
        result = check_complications([])
        assert result["level"] == "NONE"

    def test_uppercase_code_recognized(self):
        result = check_complications(["E11.9"])
        assert result["level"] == "CC"

    def test_lowercase_code_recognized(self):
        result = check_complications(["e11.9"])
        assert result["level"] == "CC"

    def test_code_with_whitespace(self):
        result = check_complications(["  I21.3  "])
        assert result["level"] == "MCC"

    def test_cc_codes_comprehensive(self):
        """Ensure common CC codes from the table are recognized."""
        common_ccs = ["E11.9", "I10", "N18.9", "I48.9", "J15.9", "F32.9",
                      "G47.3", "D64.9", "N39.0", "E87.1", "E87.6"]
        for code in common_ccs:
            result = check_complications([code])
            assert result["level"] == "CC", f"{code} not recognized as CC"

    def test_mcc_codes_comprehensive(self):
        """Ensure common MCC codes from the table are recognized."""
        common_mccs = ["I21.3", "I22.0", "J96.0", "N17.9", "R57.0",
                       "K72.0", "I50.1", "I26.0", "G93.1", "A41.9", "D65"]
        for code in common_mccs:
            result = check_complications([code])
            assert result["level"] == "MCC", f"{code} not recognized as MCC"

    def test_cc_and_mcc_sets_are_disjoint(self):
        assert MCC_SET.isdisjoint(CC_SET), "MCC and CC sets must be disjoint"


# =============================================================================
# resolve_drg() tests
# =============================================================================

class TestResolveDrg:
    @pytest.mark.parametrize("level,suffix", [
        ("MCC", "1"),
        ("CC", "9"),
        ("none", "5"),
        ("NONE", "5"),
    ])
    def test_suffix_lookup(self, level, suffix):
        assert resolve_drg("GB2", level) == f"GB2{suffix}"

    def test_resolve_drg_uppercase_level(self):
        assert resolve_drg("FR3", "MCC") == "FR31"

    def test_resolve_drg_lowercase_level(self):
        assert resolve_drg("FR3", "none") == "FR35"

    def test_resolve_drg_unknown_level_defaults_to_5(self):
        assert resolve_drg("GB2", "UNKNOWN") == "GB25"

    def test_resolve_drg_various_adrg_codes(self):
        adrg_codes = ["FR3", "ER3", "GB1", "GB2", "FM2", "IC3",
                      "GD1", "HC2", "FM1", "FL1", "OB2", "LA1"]
        for adrg in adrg_codes:
            drg_mcc = resolve_drg(adrg, "MCC")
            drg_cc = resolve_drg(adrg, "CC")
            drg_none = resolve_drg(adrg, "none")
            assert drg_mcc == f"{adrg}1"
            assert drg_cc == f"{adrg}9"
            assert drg_none == f"{adrg}5"
            # Verify suffix is the right digit
            assert drg_mcc[-1] == "1"
            assert drg_cc[-1] == "9"
            assert drg_none[-1] == "5"


# =============================================================================
# Integration: full DRG grouping pipeline
# =============================================================================

class TestDrgGroupingIntegration:
    def test_ami_with_stent_and_mcc(self):
        """STEMI + PCI + 心衰 → MDCF → FM2 → MCC → FM21"""
        mdc = get_mdc("I21.3")
        assert mdc["mdc"] == "MDCF"
        adrg = get_adrg("MDCF", ["36.0"])
        assert adrg["adrg"] == "FM2"
        comp = check_complications(["I50.1"])  # 心力衰竭
        assert comp["level"] == "MCC"
        drg = resolve_drg("FM2", "MCC")
        assert drg == "FM21"

    def test_ami_with_stent_no_complications(self):
        """STEMI + PCI，无合并症 → FM25"""
        mdc = get_mdc("I21.3")
        adrg = get_adrg("MDCF", ["36.0"])
        comp = check_complications(["Z00.0"])
        assert comp["level"] == "NONE"
        drg = resolve_drg(adrg["adrg"], "none")
        assert drg == "FM25"

    def test_cabg_with_cc(self):
        """CABG + 糖尿病 → MDCF → FM1 → CC → FM19"""
        adrg = get_adrg("MDCF", ["36.1"])
        assert adrg["adrg"] == "FM1"
        comp = check_complications(["E11.9"])
        assert comp["level"] == "CC"
        drg = resolve_drg("FM1", "CC")
        assert drg == "FM19"

    def test_appendectomy_with_copd(self):
        """阑尾炎 + COPD → MDCG → GD1 → CC → GD19"""
        mdc = get_mdc("K35.0")
        assert mdc["mdc"] == "MDCG"
        adrg = get_adrg("MDCG", ["47.0"])
        assert adrg["adrg"] == "GD1"
        comp = check_complications(["J44.9"])
        assert comp["level"] == "CC"
        drg = resolve_drg("GD1", "CC")
        assert drg == "GD19"

    def test_colorectal_cancer_with_cc(self):
        """结肠癌 + 糖尿病 → MDCG → GB1 → CC → GB19"""
        adrg = get_adrg("MDCG", ["45.7"])
        assert adrg["adrg"] == "GB1"
        comp = check_complications(["E11.9", "I10"])
        assert comp["level"] == "CC"
        drg = resolve_drg("GB1", "CC")
        assert drg == "GB19"

    def test_hip_replacement_medical_no_complication(self):
        """髋关节置换，内科无合并症 → MDCI → IC3 → none → IC35"""
        adrg = get_adrg("MDCI", ["81.51"])
        assert adrg["adrg"] == "IC3"
        comp = check_complications(["Z00.0"])
        assert comp["level"] == "NONE"
        drg = resolve_drg("IC3", "none")
        assert drg == "IC35"

    def test_pneumonia_no_surgery_no_complications(self):
        """肺炎，内科 → MDCE → ER3 → none → ER35"""
        mdc = get_mdc("J18.9")
        assert mdc["mdc"] == "MDCE"
        adrg = get_adrg("MDCE", [])
        assert adrg["type"] == "medical"
        assert adrg["adrg"] == "ER3"
        comp = check_complications([])
        assert comp["level"] == "NONE"
        drg = resolve_drg("ER3", "none")
        assert drg == "ER35"

    def test_cesarean_with_sepsis(self):
        """剖宫产 + 败血症 → MDCO → OB2 → MCC → OB21
        Use 74.9 (剖宫产术) not 74.1 (古典式剖宫产) since 74.1 is more specific and maps to OB1."""
        adrg = get_adrg("MDCO", ["74.9"])
        assert adrg["adrg"] == "OB2"
        comp = check_complications(["A41.9"])
        assert comp["level"] == "MCC"
        drg = resolve_drg("OB2", "MCC")
        assert drg == "OB21"

    def test_cholecystectomy_laparoscopic_with_cc(self):
        """腹腔镜胆囊切除 + 高血压 → MDCH → HC2 → CC → HC29"""
        adrg = get_adrg("MDCH", ["51.2"])
        assert adrg["adrg"] == "HC2"
        comp = check_complications(["I10"])
        assert comp["level"] == "CC"
        drg = resolve_drg("HC2", "CC")
        assert drg == "HC29"

    def test_elderly_patient_hip_fracture_with_mcc(self):
        """老年髋骨折 + 肺部感染 → MDCI → ID1 → MCC → ID11"""
        adrg = get_adrg("MDCI", ["79.3"])
        assert adrg["adrg"] == "ID1"
        comp = check_complications(["J96.0", "A41.9"])  # 呼吸衰竭 + 败血症
        assert comp["level"] == "MCC"
        drg = resolve_drg("ID1", "MCC")
        assert drg == "ID11"


# =============================================================================
# Data integrity tests
# =============================================================================

class TestDataIntegrity:
    def test_mdc_table_all_values_are_tuples(self):
        for k, v in MDC_TABLE.items():
            assert isinstance(v, tuple), f"{k} value is not a tuple: {v}"
            assert len(v) == 2, f"{k} tuple length != 2: {v}"

    def test_mdc_table_mdc_names_are_strings(self):
        for k, (mdc_code, mdc_name) in MDC_TABLE.items():
            assert isinstance(mdc_code, str)
            assert isinstance(mdc_name, str)

    def test_adrg_table_all_values_are_tuples(self):
        for k, v in ADRG_TABLE.items():
            assert isinstance(v, tuple)
            assert len(v) == 2

    def test_all_adrg_keys_have_valid_mdc_prefix(self):
        for key in ADRG_TABLE:
            mdc = key.split("|")[0]
            assert mdc in MDC_TABLE or mdc.startswith("MDC"), f"Invalid MDC in key: {key}"

    def test_medical_adrg_keys_are_valid_mdcs(self):
        """Every MDC key in MEDICAL_ADRG must be a valid MDC code (present in MDC_TABLE values)."""
        valid_mdcs = {v[0] for v in MDC_TABLE.values()}
        for mdc in MEDICAL_ADRG:
            assert mdc in valid_mdcs, f"Unknown MDC in MEDICAL_ADRG: {mdc}"

    def test_complication_suffix_keys_are_normalized(self):
        """NONE/none duplicate should not exist."""
        keys = list(COMPLICATION_SUFFIX.keys())
        lower_keys = [k.lower() for k in keys]
        assert len(lower_keys) == len(set(lower_keys)), "Duplicate keys in COMPLICATION_SUFFIX"

    def test_cc_and_mcc_sets_are_non_empty(self):
        assert len(CC_SET) >= 40, f"CC_SET too small: {len(CC_SET)}"
        assert len(MCC_SET) >= 20, f"MCC_SET too small: {len(MCC_SET)}"

    def test_load_drg_graph_returns_list(self):
        result = load_drg_graph()
        assert isinstance(result, list)
        assert len(result) > 0
        for edge in result:
            assert "source" in edge
            assert "relation" in edge
            assert "target" in edge
