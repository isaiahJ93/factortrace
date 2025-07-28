def add_navigation_structure(body: ET.Element, data: Dict[str, Any]) -> None:
    """Add navigation sidebar for easy navigation through the report"""
    nav = ET.SubElement(body, 'nav', {'class': 'navigation', 'id': 'navigation'})
    
    # Navigation header
    nav_header = ET.SubElement(nav, 'div', {'class': 'nav-header'})
    h3 = ET.SubElement(nav_header, 'h3')
    h3.text = 'ESRS E1 Navigation'
    
    # Navigation sections
    nav_sections = [
        ('executive', 'Executive Summary'),
        ('materiality', 'Materiality Assessment'),
        ('governance', 'Governance (E1-1)'),
        ('transition-plan', 'Transition Plan (E1-1)'),
        ('policies', 'Policies (E1-2)'),
        ('actions', 'Actions & Resources (E1-3)'),
        ('targets', 'Targets (E1-4)'),
        ('energy', 'Energy (E1-5)'),
        ('emissions', 'GHG Emissions (E1-6)'),
        ('removals', 'Removals (E1-7)'),
        ('pricing', 'Carbon Pricing (E1-8)'),
        ('financial', 'Financial Effects (E1-9)'),
        ('eu-taxonomy', 'EU Taxonomy'),
        ('value-chain', 'Value Chain'),
        ('methodology', 'Methodology'),
        ('assurance', 'Assurance')
    ]
    
    nav_section = ET.SubElement(nav, 'div', {'class': 'nav-section'})
    
    for nav_id, nav_text in nav_sections:
        nav_item = ET.SubElement(nav_section, 'div', {
            'class': 'nav-item',
            'data-target': nav_id
        })
        nav_item.text = nav_text

def add_executive_summary(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add executive summary with key performance indicators"""
    exec_section = ET.SubElement(parent, 'section', {
        'class': 'executive-summary',
        'id': 'executive'
    })
    
    h1 = ET.SubElement(exec_section, 'h1')
    h1.text = f"ESRS E1 Climate Disclosures - {data.get('organization', 'Organization Name')}"
    
    # Key metrics dashboard
    kpi_dashboard = ET.SubElement(exec_section, 'div', {'class': 'kpi-dashboard'})
    kpi_grid = ET.SubElement(kpi_dashboard, 'div', {'class': 'kpi-grid'})
    
    # Extract key metrics
    emissions = data.get('emissions', {})
    total_emissions = sum([
        emissions.get('scope1', 0),
        emissions.get('scope2_market', emissions.get('scope2_location', 0)),
        sum(data.get('scope3_detailed', {}).get(f'category_{i}', {}).get('emissions_tco2e', 0) 
            for i in range(1, 16) 
            if not data.get('scope3_detailed', {}).get(f'category_{i}', {}).get('excluded', False))
    ])
    
    # KPI cards
    kpis = [
        {
            'label': 'Total GHG Emissions',
            'value': f"{total_emissions:,.0f}",
            'unit': 'tCO₂e',
            'class': 'primary',
            'xbrl_element': 'esrs-e1:TotalGHGEmissions'
        },
        {
            'label': 'Year-over-Year Change',
            'value': f"{data.get('emissions_change_percent', 0):+.1f}",
            'unit': '%',
            'class': 'trend',
            'xbrl_element': 'esrs-e1:EmissionsChangePercent'
        },
        {
            'label': 'Data Quality Score',
            'value': f"{data.get('data_quality_score', 0):.0f}",
            'unit': '/100',
            'class': 'quality',
            'xbrl_element': 'esrs-e1:DataQualityScore'
        },
        {
            'label': 'Net Zero Target',
            'value': str(data.get('transition_plan', {}).get('net_zero_target_year', 'TBD')),
            'unit': '',
            'class': 'target',
            'xbrl_element': 'esrs-e1:NetZeroTargetYear'
        }
    ]
    
    for kpi in kpis:
        kpi_card = ET.SubElement(kpi_grid, 'div', {'class': f'kpi-card {kpi["class"]}'})
        
        label_div = ET.SubElement(kpi_card, 'div', {'class': 'kpi-label'})
        label_div.text = kpi['label']
        
        value_div = ET.SubElement(kpi_card, 'div', {'class': 'kpi-value'})
        if kpi['xbrl_element'] and kpi['value'] not in ['TBD', 'N/A']:
            # Create XBRL tag
            create_enhanced_xbrl_tag(
                value_div,
                'nonFraction' if kpi['unit'] else 'nonNumeric',
                kpi['xbrl_element'],
                'c-current',
                kpi['value'].replace(',', ''),
                unit_ref='u-tCO2e' if 'tCO₂e' in kpi['unit'] else 'u-percent' if '%' in kpi['unit'] else None,
                decimals='0' if 'tCO₂e' in kpi['unit'] else '1' if '%' in kpi['unit'] else None
            )
        else:
            value_div.text = kpi['value']
        
        if kpi['unit']:
            unit_div = ET.SubElement(kpi_card, 'div', {'class': 'kpi-unit'})
            unit_div.text = kpi['unit']

def add_report_header(parent: ET.Element, data: Dict[str, Any], doc_id: str, period: int, org_name: str) -> None:
    """Add report header with metadata"""
    header_section = ET.SubElement(parent, 'section', {'class': 'report-header'})
    
    # Report metadata
    metadata_div = ET.SubElement(header_section, 'div', {'class': 'report-metadata'})
    
    metadata_items = [
        ('Organization', org_name),
        ('LEI', data.get('lei', 'PENDING')),
        ('Reporting Period', str(period)),
        ('Document ID', doc_id),
        ('ESRS Standard', 'E1 - Climate Change'),
        ('Consolidation Scope', data.get('consolidation_scope', 'Individual'))
    ]
    
    for label, value in metadata_items:
        p = ET.SubElement(metadata_div, 'p')
        strong = ET.SubElement(p, 'strong')
        strong.text = f"{label}: "
        strong.tail = value

def add_materiality_assessment(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add double materiality assessment section"""
    mat_section = ET.SubElement(parent, 'section', {
        'class': 'materiality-assessment',
        'id': 'materiality'
    })
    
    h2 = ET.SubElement(mat_section, 'h2')
    h2.text = 'Double Materiality Assessment'
    
    mat_data = data.get('materiality_assessment', {})
    
    if mat_data:
        # Impact materiality
        impact_div = ET.SubElement(mat_section, 'div', {'class': 'impact-materiality'})
        h3_impact = ET.SubElement(impact_div, 'h3')
        h3_impact.text = 'Impact Materiality'
        
        p_impact = ET.SubElement(impact_div, 'p')
        p_impact.text = 'Climate change has been assessed as material from an impact perspective: '
        create_enhanced_xbrl_tag(
            p_impact,
            'nonNumeric',
            'esrs-e1:ImpactMaterialityAssessment',
            'c-current',
            'Material' if mat_data.get('impact_material', True) else 'Not Material',
            xml_lang='en'
        )
        
        # Financial materiality
        financial_div = ET.SubElement(mat_section, 'div', {'class': 'financial-materiality'})
        h3_financial = ET.SubElement(financial_div, 'h3')
        h3_financial.text = 'Financial Materiality'
        
        p_financial = ET.SubElement(financial_div, 'p')
        p_financial.text = 'Climate change has been assessed as material from a financial perspective: '
        create_enhanced_xbrl_tag(
            p_financial,
            'nonNumeric',
            'esrs-e1:FinancialMaterialityAssessment',
            'c-current',
            'Material' if mat_data.get('financial_material', True) else 'Not Material',
            xml_lang='en'
        )
    else:
        p = ET.SubElement(mat_section, 'p')
        p.text = 'Climate change has been identified as material through our double materiality assessment process.'

def add_governance_section(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add governance section per ESRS 2 GOV-1 requirements"""
    gov_section = ET.SubElement(parent, 'section', {
        'class': 'governance',
        'id': 'governance'
    })
    
    h2 = ET.SubElement(gov_section, 'h2')
    h2.text = 'Governance of Climate-Related Matters'
    
    gov_data = data.get('governance', {})
    
    # Board oversight
    board_div = ET.SubElement(gov_section, 'div', {'class': 'board-oversight'})
    h3_board = ET.SubElement(board_div, 'h3')
    h3_board.text = 'Board Oversight'
    
    p_board = ET.SubElement(board_div, 'p')
    p_board.text = 'Board oversight of climate-related risks and opportunities: '
    create_enhanced_xbrl_tag(
        p_board,
        'nonNumeric',
        'esrs-2:BoardOversightClimate',
        'c-current',
        'Yes' if gov_data.get('board_oversight', False) else 'No',
        xml_lang='en'
    )
    
    if gov_data.get('board_meetings_climate'):
        p_meetings = ET.SubElement(board_div, 'p')
        p_meetings.text = 'Board meetings discussing climate in reporting period: '
        create_enhanced_xbrl_tag(
            p_meetings,
            'nonFraction',
            'esrs-2:BoardMeetingsClimate',
            'c-current',
            gov_data['board_meetings_climate'],
            decimals='0'
        )
    
    # Management responsibility
    mgmt_div = ET.SubElement(gov_section, 'div', {'class': 'management-responsibility'})
    h3_mgmt = ET.SubElement(mgmt_div, 'h3')
    h3_mgmt.text = 'Management Responsibility'
    
    p_mgmt = ET.SubElement(mgmt_div, 'p')
    p_mgmt.text = 'Executive management responsibility for climate matters: '
    create_enhanced_xbrl_tag(
        p_mgmt,
        'nonNumeric',
        'esrs-2:ManagementResponsibilityClimate',
        'c-current',
        'Yes' if gov_data.get('management_responsibility', False) else 'No',
        xml_lang='en'
    )
    
    # Climate expertise
    if gov_data.get('climate_expertise'):
        expertise_div = ET.SubElement(gov_section, 'div', {'class': 'climate-expertise'})
        h3_expertise = ET.SubElement(expertise_div, 'h3')
        h3_expertise.text = 'Climate Expertise'
        
        p_expertise = ET.SubElement(expertise_div, 'p')
        create_enhanced_xbrl_tag(
            p_expertise,
            'nonNumeric',
            'esrs-2:ClimateExpertiseDescription',
            'c-current',
            gov_data['climate_expertise'],
            xml_lang='en'
        )
    
    # Incentives
    if gov_data.get('climate_linked_compensation'):
        incentive_div = ET.SubElement(gov_section, 'div', {'class': 'climate-incentives'})
        p_incentive = ET.SubElement(incentive_div, 'p')
        p_incentive.text = 'Executive compensation linked to climate performance: '
        create_enhanced_xbrl_tag(
            p_incentive,
            'nonNumeric',
            'esrs-2:ClimateLinkedCompensation',
            'c-current',
            'Yes',
            xml_lang='en'
        )

def add_transition_plan_section(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add E1-1 transition plan section with complete disclosure"""
    tp_section = ET.SubElement(parent, 'section', {
        'class': 'transition-plan',
        'id': 'transition-plan'
    })
    
    h2 = ET.SubElement(tp_section, 'h2')
    h2.text = 'E1-1: Transition Plan for Climate Change Mitigation'
    
    tp_data = data.get('transition_plan', {})
    
    # Transition plan adoption status
    p_adopted = ET.SubElement(tp_section, 'p')
    p_adopted.text = 'Transition plan adopted: '
    create_enhanced_xbrl_tag(
        p_adopted,
        'nonNumeric',
        'esrs-e1:TransitionPlanAdopted',
        'c-current',
        'Yes' if tp_data.get('adopted', False) else 'No',
        xml_lang='en'
    )
    
    if tp_data.get('adopted'):
        # Adoption date
        if tp_data.get('adoption_date'):
            p_date = ET.SubElement(tp_section, 'p')
            p_date.text = 'Adoption date: '
            create_enhanced_xbrl_tag(
                p_date,
                'nonNumeric',
                'esrs-e1:TransitionPlanAdoptionDate',
                'c-current',
                tp_data['adoption_date'],
                format='ixt:date'
            )
        
        # Net zero target
        nz_div = ET.SubElement(tp_section, 'div', {'class': 'net-zero-target'})
        h3_nz = ET.SubElement(nz_div, 'h3')
        h3_nz.text = 'Net Zero Target'
        
        p_nz = ET.SubElement(nz_div, 'p')
        p_nz.text = 'Net zero target year: '
        create_enhanced_xbrl_tag(
            p_nz,
            'nonFraction',
            'esrs-e1:NetZeroTargetYear',
            'c-current',
            tp_data.get('net_zero_target_year', 2050),
            decimals='0'
        )
        
        # Decarbonization levers
        if tp_data.get('decarbonization_levers'):
            levers_div = ET.SubElement(tp_section, 'div', {'class': 'decarbonization-levers'})
            h3_levers = ET.SubElement(levers_div, 'h3')
            h3_levers.text = 'Key Decarbonization Levers'
            
            ul = ET.SubElement(levers_div, 'ul')
            for lever in tp_data['decarbonization_levers']:
                li = ET.SubElement(ul, 'li')
                li.text = lever
        
        # Financial planning
        if tp_data.get('financial_planning'):
            fin_div = ET.SubElement(tp_section, 'div', {'class': 'financial-planning'})
            h3_fin = ET.SubElement(fin_div, 'h3')
            h3_fin.text = 'Financial Planning'
            
            if tp_data['financial_planning'].get('capex_allocated'):
                p_capex = ET.SubElement(fin_div, 'p')
                p_capex.text = 'CapEx allocated for transition: €'
                create_enhanced_xbrl_tag(
                    p_capex,
                    'nonFraction',
                    'esrs-e1:TransitionCapEx',
                    'c-current',
                    tp_data['financial_planning']['capex_allocated'],
                    unit_ref='u-EUR-millions',
                    decimals='0'
                )
                p_capex.tail = ' million'
        
        # Locked-in emissions
        if tp_data.get('locked_in_emissions'):
            locked_div = ET.SubElement(tp_section, 'div', {'class': 'locked-in-emissions'})
            h3_locked = ET.SubElement(locked_div, 'h3')
            h3_locked.text = 'Locked-in GHG Emissions'
            
            p_locked = ET.SubElement(locked_div, 'p')
            create_enhanced_xbrl_tag(
                p_locked,
                'nonNumeric',
                'esrs-e1:LockedInEmissionsDisclosure',
                'c-current',
                tp_data['locked_in_emissions'],
                xml_lang='en'
            )
        
        # Just transition
        if tp_data.get('just_transition'):
            just_div = ET.SubElement(tp_section, 'div', {'class': 'just-transition'})
            h3_just = ET.SubElement(just_div, 'h3')
            h3_just.text = 'Just Transition Considerations'
            
            p_just = ET.SubElement(just_div, 'p')
            create_enhanced_xbrl_tag(
                p_just,
                'nonNumeric',
                'esrs-e1:JustTransitionDisclosure',
                'c-current',
                tp_data['just_transition'],
                xml_lang='en'
            )
            
            # Cross-reference to S1
            cross_ref = ET.SubElement(just_div, 'p', {'class': 'cross-reference'})
            cross_ref.text = '→ See ESRS S1 disclosures for detailed workforce transition impacts'

def add_climate_policy_section_enhanced(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add E1-2 climate change mitigation and adaptation policies"""
    policy_section = ET.SubElement(parent, 'section', {
        'class': 'climate-policies',
        'id': 'policies'
    })
    
    h2 = ET.SubElement(policy_section, 'h2')
    h2.text = 'E1-2: Policies Related to Climate Change Mitigation and Adaptation'
    
    policy_data = data.get('climate_policy', {})
    
    # Policy existence
    p_has_policy = ET.SubElement(policy_section, 'p')
    p_has_policy.text = 'Climate policy in place: '
    create_enhanced_xbrl_tag(
        p_has_policy,
        'nonNumeric',
        'esrs-e1:HasClimatePolicy',
        'c-current',
        'Yes' if policy_data.get('has_climate_policy', False) else 'No',
        xml_lang='en'
    )
    
    if policy_data.get('has_climate_policy'):
        # Policy description
        if policy_data.get('policy_description'):
            desc_div = ET.SubElement(policy_section, 'div', {'class': 'policy-description'})
            p_desc = ET.SubElement(desc_div, 'p')
            create_enhanced_xbrl_tag(
                p_desc,
                'nonNumeric',
                'esrs-e1:ClimatePolicyDescription',
                'c-current',
                policy_data['policy_description'],
                xml_lang='en'
            )
        
        # Policy adoption date
        if policy_data.get('policy_adoption_date'):
            p_date = ET.SubElement(policy_section, 'p')
            p_date.text = 'Policy adoption date: '
            create_enhanced_xbrl_tag(
                p_date,
                'nonNumeric',
                'esrs-e1:PolicyAdoptionDate',
                'c-current',
                policy_data['policy_adoption_date'],
                format='ixt:date'
            )
        
        # Coverage
        coverage_div = ET.SubElement(policy_section, 'div', {'class': 'policy-coverage'})
        h3_coverage = ET.SubElement(coverage_div, 'h3')
        h3_coverage.text = 'Policy Coverage'
        
        coverage_items = [
            ('covers_own_operations', 'Own operations'),
            ('covers_value_chain', 'Value chain'),
            ('covers_products_services', 'Products and services')
        ]
        
        ul_coverage = ET.SubElement(coverage_div, 'ul')
        for key, label in coverage_items:
            if policy_data.get(key, False):
                li = ET.SubElement(ul_coverage, 'li')
                li.text = f"✓ {label}"
        
        # Integration with business strategy
        if policy_data.get('integrated_with_strategy'):
            p_integrated = ET.SubElement(policy_section, 'p')
            p_integrated.text = 'Policy integrated with business strategy: '
            create_enhanced_xbrl_tag(
                p_integrated,
                'nonNumeric',
                'esrs-e1:PolicyIntegratedWithStrategy',
                'c-current',
                'Yes',
                xml_lang='en'
            )

def add_climate_actions_section_enhanced(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add E1-3 actions and resources section"""
    actions_section = ET.SubElement(parent, 'section', {
        'class': 'climate-actions',
        'id': 'actions'
    })
    
    h2 = ET.SubElement(actions_section, 'h2')
    h2.text = 'E1-3: Actions and Resources Related to Climate Change'
    
    actions_data = data.get('climate_actions', {})
    
    # Climate actions table
    if actions_data.get('actions'):
        actions_table = ET.SubElement(actions_section, 'table', {'class': 'actions-table'})
        thead = ET.SubElement(actions_table, 'thead')
        tr_header = ET.SubElement(thead, 'tr')
        
        headers = ['Action', 'Type', 'Timeline', 'Investment (€M)', 'Expected Impact']
        for header in headers:
            th = ET.SubElement(tr_header, 'th')
            th.text = header
        
        tbody = ET.SubElement(actions_table, 'tbody')
        
        for idx, action in enumerate(actions_data['actions']):
            tr = ET.SubElement(tbody, 'tr')
            
            # Action description
            td_desc = ET.SubElement(tr, 'td')
            create_enhanced_xbrl_tag(
                td_desc,
                'nonNumeric',
                f'esrs-e1:ClimateAction{idx+1}Description',
                'c-current',
                action['description'],
                xml_lang='en'
            )
            
            # Type
            td_type = ET.SubElement(tr, 'td')
            td_type.text = action.get('type', 'Mitigation')
            
            # Timeline
            td_timeline = ET.SubElement(tr, 'td')
            td_timeline.text = action.get('timeline', 'Ongoing')
            
            # Investment
            td_investment = ET.SubElement(tr, 'td')
            if action.get('investment_meur'):
                create_enhanced_xbrl_tag(
                    td_investment,
                    'nonFraction',
                    f'esrs-e1:ClimateAction{idx+1}Investment',
                    'c-current',
                    action['investment_meur'],
                    unit_ref='u-EUR-millions',
                    decimals='0'
                )
            else:
                td_investment.text = 'TBD'
            
            # Expected impact
            td_impact = ET.SubElement(tr, 'td')
            td_impact.text = action.get('expected_impact', 'Under assessment')
    
    # Total resources
    resources_div = ET.SubElement(actions_section, 'div', {'class': 'total-resources'})
    h3_resources = ET.SubElement(resources_div, 'h3')
    h3_resources.text = 'Total Resources Allocated'
    
    # CapEx
    if actions_data.get('capex_climate_eur'):
        p_capex = ET.SubElement(resources_div, 'p')
        p_capex.text = 'Climate-related CapEx: €'
        create_enhanced_xbrl_tag(
            p_capex,
            'nonFraction',
            'esrs-e1:ClimateCapEx',
            'c-current',
            actions_data['capex_climate_eur'] / 1_000_000,
            unit_ref='u-EUR-millions',
            decimals='0'
        )
        p_capex.tail = ' million'
    
    # OpEx
    if actions_data.get('opex_climate_eur'):
        p_opex = ET.SubElement(resources_div, 'p')
        p_opex.text = 'Climate-related OpEx: €'
        create_enhanced_xbrl_tag(
            p_opex,
            'nonFraction',
            'esrs-e1:ClimateOpEx',
            'c-current',
            actions_data['opex_climate_eur'] / 1_000_000,
            unit_ref='u-EUR-millions',
            decimals='0'
        )
        p_opex.tail = ' million'
    
    # FTE
    if actions_data.get('fte_dedicated'):
        p_fte = ET.SubElement(resources_div, 'p')
        p_fte.text = 'FTEs dedicated to climate actions: '
        create_enhanced_xbrl_tag(
            p_fte,
            'nonFraction',
            'esrs-e1:ClimateFTE',
            'c-current',
            actions_data['fte_dedicated'],
            unit_ref='u-FTE',
            decimals='0'
        )

def add_targets_section(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add E1-4 targets section"""
    targets_section = ET.SubElement(parent, 'section', {
        'class': 'climate-targets',
        'id': 'targets'
    })
    
    h2 = ET.SubElement(targets_section, 'h2')
    h2.text = 'E1-4: GHG Emission Reduction Targets'
    
    targets_data = data.get('targets', {})
    
    # Base year information
    if targets_data.get('base_year'):
        base_div = ET.SubElement(targets_section, 'div', {'class': 'base-year-info'})
        p_base = ET.SubElement(base_div, 'p')
        p_base.text = 'Base year: '
        create_enhanced_xbrl_tag(
            p_base,
            'nonFraction',
            'esrs-e1:TargetBaseYear',
            'c-current',
            targets_data['base_year'],
            decimals='0'
        )
        
        if targets_data.get('base_year_emissions'):
            p_base_emissions = ET.SubElement(base_div, 'p')
            p_base_emissions.text = 'Base year emissions: '
            create_enhanced_xbrl_tag(
                p_base_emissions,
                'nonFraction',
                'esrs-e1:BaseYearEmissions',
                'c-base',
                targets_data['base_year_emissions'],
                unit_ref='u-tCO2e',
                decimals='0'
            )
            p_base_emissions.tail = ' tCO₂e'
    
    # Targets table
    if targets_data.get('targets'):
        targets_table = ET.SubElement(targets_section, 'table', {'class': 'targets-table'})
        thead = ET.SubElement(targets_table, 'thead')
        tr_header = ET.SubElement(thead, 'tr')
        
        headers = ['Target', 'Scope', 'Target Year', 'Reduction %', 'Progress %', 'Status']
        for header in headers:
            th = ET.SubElement(tr_header, 'th')
            th.text = header
        
        tbody = ET.SubElement(targets_table, 'tbody')
        
        for idx, target in enumerate(targets_data['targets']):
            tr = ET.SubElement(tbody, 'tr')
            
            # Target description
            td_desc = ET.SubElement(tr, 'td')
            create_enhanced_xbrl_tag(
                td_desc,
                'nonNumeric',
                f'esrs-e1:Target{idx+1}Description',
                'c-current',
                target['description'],
                xml_lang='en'
            )
            
            # Scope
            td_scope = ET.SubElement(tr, 'td')
            td_scope.text = target.get('scope', 'All scopes')
            
            # Target year
            td_year = ET.SubElement(tr, 'td')
            create_enhanced_xbrl_tag(
                td_year,
                'nonFraction',
                f'esrs-e1:Target{idx+1}Year',
                f'c-target-{target["target_year"]}',
                target['target_year'],
                decimals='0'
            )
            
            # Reduction percentage
            td_reduction = ET.SubElement(tr, 'td')
            create_enhanced_xbrl_tag(
                td_reduction,
                'nonFraction',
                f'esrs-e1:Target{idx+1}ReductionPercent',
                'c-current',
                target['reduction_percent'],
                unit_ref='u-percent',
                decimals='0'
            )
            td_reduction.tail = '%'
            
            # Progress
            td_progress = ET.SubElement(tr, 'td')
            if 'progress_percent' in target:
                create_enhanced_xbrl_tag(
                    td_progress,
                    'nonFraction',
                    f'esrs-e1:Target{idx+1}ProgressPercent',
                    'c-current',
                    target['progress_percent'],
                    unit_ref='u-percent',
                    decimals='1'
                )
                td_progress.tail = '%'
            else:
                td_progress.text = 'TBD'
            
            # Status
            td_status = ET.SubElement(tr, 'td')
            status = target.get('status', 'On track')
            td_status.set('class', f'status-{status.lower().replace(" ", "-")}')
            td_status.text = status
    
    # SBTi validation
    if targets_data.get('sbti_validated'):
        sbti_div = ET.SubElement(targets_section, 'div', {'class': 'sbti-validation'})
        p_sbti = ET.SubElement(sbti_div, 'p', {'class': 'sbti-badge'})
        p_sbti.text = '✓ Science-Based Targets Validated'
        
        if targets_data.get('sbti_ambition'):
            p_ambition = ET.SubElement(sbti_div, 'p')
            p_ambition.text = 'SBTi ambition level: '
            create_enhanced_xbrl_tag(
                p_ambition,
                'nonNumeric',
                'esrs-e1:SBTiAmbitionLevel',
                'c-current',
                targets_data['sbti_ambition'],
                xml_lang='en'
            )

def add_energy_consumption_section_enhanced(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add E1-5 energy consumption and mix section"""
    energy_section = ET.SubElement(parent, 'section', {
        'class': 'energy-consumption',
        'id': 'energy'
    })
    
    h2 = ET.SubElement(energy_section, 'h2')
    h2.text = 'E1-5: Energy Consumption and Mix'
    
    # Extract energy data with fallback handling
    energy_data = {}
    if 'esrs_e1_data' in data and 'energy_consumption' in data['esrs_e1_data']:
        energy_data = data['esrs_e1_data']['energy_consumption']
    elif 'energy_consumption' in data:
        energy_data = data['energy_consumption']
    elif 'energy' in data:
        energy_data = data['energy']
    
    # Energy consumption table
    energy_table = ET.SubElement(energy_section, 'table', {'class': 'energy-table'})
    thead = ET.SubElement(energy_table, 'thead')
    tr_header = ET.SubElement(thead, 'tr')
    
    headers = ['Energy Type', 'Total Consumption (MWh)', 'Renewable (MWh)', 'Renewable %']
    for header in headers:
        th = ET.SubElement(tr_header, 'th')
        th.text = header
    
    tbody = ET.SubElement(energy_table, 'tbody')
    
    # Energy types
    energy_types = [
        ('Electricity', 'electricity_mwh', 'renewable_electricity_mwh'),
        ('Heating & Cooling', 'heating_cooling_mwh', 'renewable_heating_cooling_mwh'),
        ('Steam', 'steam_mwh', 'renewable_steam_mwh'),
        ('Fuel Combustion', 'fuel_combustion_mwh', 'renewable_fuels_mwh')
    ]
    
    total_consumption = 0
    total_renewable = 0
    
    for label, consumption_key, renewable_key in energy_types:
        consumption = energy_data.get(consumption_key, 0)
        renewable = energy_data.get(renewable_key, 0)
        total_consumption += consumption
        total_renewable += renewable
        
        if consumption > 0:
            tr = ET.SubElement(tbody, 'tr')
            
            # Energy type
            td_type = ET.SubElement(tr, 'td')
            td_type.text = label
            
            # Total consumption
            td_consumption = ET.SubElement(tr, 'td')
            create_enhanced_xbrl_tag(
                td_consumption,
                'nonFraction',
                f'esrs-e1:EnergyConsumption{label.replace(" & ", "").replace(" ", "")}',
                'c-current',
                consumption,
                unit_ref='u-MWh',
                decimals='0'
            )
            
            # Renewable
            td_renewable = ET.SubElement(tr, 'td')
            create_enhanced_xbrl_tag(
                td_renewable,
                'nonFraction',
                f'esrs-e1:RenewableEnergy{label.replace(" & ", "").replace(" ", "")}',
                'c-current',
                renewable,
                unit_ref='u-MWh',
                decimals='0'
            )
            
            # Renewable percentage
            td_percent = ET.SubElement(tr, 'td')
            if consumption > 0:
                renewable_percent = (renewable / consumption) * 100
                create_enhanced_xbrl_tag(
                    td_percent,
                    'nonFraction',
                    f'esrs-e1:RenewablePercentage{label.replace(" & ", "").replace(" ", "")}',
                    'c-current',
                    renewable_percent,
                    unit_ref='u-percent',
                    decimals='1'
                )
                td_percent.tail = '%'
            else:
                td_percent.text = 'N/A'
    
    # Total row
    tr_total = ET.SubElement(tbody, 'tr', {'class': 'total-row'})
    
    td_total_label = ET.SubElement(tr_total, 'td')
    td_total_label.text = 'TOTAL'
    
    td_total_consumption = ET.SubElement(tr_total, 'td')
    create_enhanced_xbrl_tag(
        td_total_consumption,
        'nonFraction',
        'esrs-e1:TotalEnergyConsumption',
        'c-current',
        total_consumption,
        unit_ref='u-MWh',
        decimals='0'
    )
    
    td_total_renewable = ET.SubElement(tr_total, 'td')
    create_enhanced_xbrl_tag(
        td_total_renewable,
        'nonFraction',
        'esrs-e1:TotalRenewableEnergy',
        'c-current',
        total_renewable,
        unit_ref='u-MWh',
        decimals='0'
    )
    
    td_total_percent = ET.SubElement(tr_total, 'td')
    if total_consumption > 0:
        total_renewable_percent = (total_renewable / total_consumption) * 100
        create_enhanced_xbrl_tag(
            td_total_percent,
            'nonFraction',
            'esrs-e1:TotalRenewableEnergyPercentage',
            'c-current',
            total_renewable_percent,
            unit_ref='u-percent',
            decimals='1'
        )
        td_total_percent.tail = '%'
    else:
        td_total_percent.text = 'N/A'
    
    # Energy intensity
    if energy_data.get('energy_intensity_value'):
        intensity_div = ET.SubElement(energy_section, 'div', {'class': 'energy-intensity'})
        h3_intensity = ET.SubElement(intensity_div, 'h3')
        h3_intensity.text = 'Energy Intensity'
        
        p_intensity = ET.SubElement(intensity_div, 'p')
        p_intensity.text = 'Energy intensity: '
        create_enhanced_xbrl_tag(
            p_intensity,
            'nonFraction',
            'esrs-e1:EnergyIntensity',
            'c-current',
            energy_data['energy_intensity_value'],
            unit_ref='u-MWh-per-EUR',
            decimals='2'
        )
        p_intensity.tail = f' {energy_data.get("energy_intensity_unit", "MWh/million EUR")}'

def add_ghg_emissions_section(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add E1-6 GHG emissions section with complete breakdown"""
    emissions_section = ET.SubElement(parent, 'section', {
        'class': 'ghg-emissions',
        'id': 'emissions'
    })
    
    h2 = ET.SubElement(emissions_section, 'h2')
    h2.text = 'E1-6: Gross Scopes 1, 2, 3 and Total GHG Emissions'
    
    emissions_data = data.get('emissions', {})
    
    # GHG emissions overview table
    emissions_table = ET.SubElement(emissions_section, 'table', {'class': 'emissions-overview-table'})
    thead = ET.SubElement(emissions_table, 'thead')
    tr_header = ET.SubElement(thead, 'tr')
    
    headers = ['Emission Scope', 'Current Year (tCO₂e)', 'Previous Year (tCO₂e)', 'Change %']
    for header in headers:
        th = ET.SubElement(tr_header, 'th')
        th.text = header
    
    tbody = ET.SubElement(emissions_table, 'tbody')
    
    # Scope 1
    tr_scope1 = ET.SubElement(tbody, 'tr')
    td_s1_label = ET.SubElement(tr_scope1, 'td')
    td_s1_label.text = 'Scope 1 (Direct emissions)'
    
    td_s1_current = ET.SubElement(tr_scope1, 'td')
    create_enhanced_xbrl_tag(
        td_s1_current,
        'nonFraction',
        'esrs-e1:GrossScope1Emissions',
        'c-current',
        emissions_data.get('scope1', 0),
        unit_ref='u-tCO2e',
        decimals='0'
    )
    
    td_s1_previous = ET.SubElement(tr_scope1, 'td')
    if data.get('previous_year_emissions', {}).get('scope1'):
        create_enhanced_xbrl_tag(
            td_s1_previous,
            'nonFraction',
            'esrs-e1:GrossScope1Emissions',
            'c-previous',
            data['previous_year_emissions']['scope1'],
            unit_ref='u-tCO2e',
            decimals='0'
        )
    else:
        td_s1_previous.text = 'N/A'
    
    td_s1_change = ET.SubElement(tr_scope1, 'td')
    if data.get('previous_year_emissions', {}).get('scope1'):
        change_pct = calculate_percentage_change(
            data['previous_year_emissions']['scope1'],
            emissions_data.get('scope1', 0)
        )
        td_s1_change.text = f"{change_pct:+.1f}%"
    else:
        td_s1_change.text = 'N/A'
    
    # Scope 2 - Location-based
    tr_scope2_loc = ET.SubElement(tbody, 'tr')
    td_s2l_label = ET.SubElement(tr_scope2_loc, 'td')
    td_s2l_label.text = 'Scope 2 (Location-based)'
    
    td_s2l_current = ET.SubElement(tr_scope2_loc, 'td')
    create_enhanced_xbrl_tag(
        td_s2l_current,
        'nonFraction',
        'esrs-e1:GrossScope2LocationBased',
        'c-current',
        emissions_data.get('scope2_location', 0),
        unit_ref='u-tCO2e',
        decimals='0'
    )
    
    td_s2l_previous = ET.SubElement(tr_scope2_loc, 'td')
    if data.get('previous_year_emissions', {}).get('scope2_location'):
        create_enhanced_xbrl_tag(
            td_s2l_previous,
            'nonFraction',
            'esrs-e1:GrossScope2LocationBased',
            'c-previous',
            data['previous_year_emissions']['scope2_location'],
            unit_ref='u-tCO2e',
            decimals='0'
        )
    else:
        td_s2l_previous.text = 'N/A'
    
    td_s2l_change = ET.SubElement(tr_scope2_loc, 'td')
    td_s2l_change.text = 'N/A'
    
    # Scope 2 - Market-based
    if emissions_data.get('scope2_market') is not None:
        tr_scope2_mkt = ET.SubElement(tbody, 'tr')
        td_s2m_label = ET.SubElement(tr_scope2_mkt, 'td')
        td_s2m_label.text = 'Scope 2 (Market-based)'
        
        td_s2m_current = ET.SubElement(tr_scope2_mkt, 'td')
        create_enhanced_xbrl_tag(
            td_s2m_current,
            'nonFraction',
            'esrs-e1:GrossScope2MarketBased',
            'c-current',
            emissions_data['scope2_market'],
            unit_ref='u-tCO2e',
            decimals='0'
        )
        
        td_s2m_previous = ET.SubElement(tr_scope2_mkt, 'td')
        if data.get('previous_year_emissions', {}).get('scope2_market'):
            create_enhanced_xbrl_tag(
                td_s2m_previous,
                'nonFraction',
                'esrs-e1:GrossScope2MarketBased',
                'c-previous',
                data['previous_year_emissions']['scope2_market'],
                unit_ref='u-tCO2e',
                decimals='0'
            )
        else:
            td_s2m_previous.text = 'N/A'
        
        td_s2m_change = ET.SubElement(tr_scope2_mkt, 'td')
        td_s2m_change.text = 'N/A'
    
    # Scope 3 total
    scope3_total = sum(
        data.get('scope3_detailed', {}).get(f'category_{i}', {}).get('emissions_tco2e', 0) 
        for i in range(1, 16) 
        if not data.get('scope3_detailed', {}).get(f'category_{i}', {}).get('excluded', False)
    )
    
    tr_scope3 = ET.SubElement(tbody, 'tr')
    td_s3_label = ET.SubElement(tr_scope3, 'td')
    td_s3_label.text = 'Scope 3 (Value chain emissions)'
    
    td_s3_current = ET.SubElement(tr_scope3, 'td')
    create_enhanced_xbrl_tag(
        td_s3_current,
        'nonFraction',
        'esrs-e1:GrossScope3Emissions',
        'c-current',
        scope3_total,
        unit_ref='u-tCO2e',
        decimals='0'
    )
    
    td_s3_previous = ET.SubElement(tr_scope3, 'td')
    td_s3_previous.text = 'N/A'
    
    td_s3_change = ET.SubElement(tr_scope3, 'td')
    td_s3_change.text = 'N/A'
    
    # Total emissions
    total_emissions = (
        emissions_data.get('scope1', 0) +
        emissions_data.get('scope2_market', emissions_data.get('scope2_location', 0)) +
        scope3_total
    )
    
    tr_total = ET.SubElement(tbody, 'tr', {'class': 'grand-total'})
    td_total_label = ET.SubElement(tr_total, 'td')
    td_total_label.text = 'TOTAL GHG EMISSIONS'
    
    td_total_current = ET.SubElement(tr_total, 'td')
    create_enhanced_xbrl_tag(
        td_total_current,
        'nonFraction',
        'esrs-e1:TotalGHGEmissions',
        'c-current',
        total_emissions,
        unit_ref='u-tCO2e',
        decimals='0'
    )
    
    td_total_previous = ET.SubElement(tr_total, 'td')
    td_total_previous.text = 'N/A'
    
    td_total_change = ET.SubElement(tr_total, 'td')
    td_total_change.text = 'N/A'
    
    # Scope 3 breakdown
    if data.get('scope3_detailed'):
        scope3_div = ET.SubElement(emissions_section, 'div', {'class': 'scope3-breakdown'})
        h3_scope3 = ET.SubElement(scope3_div, 'h3')
        h3_scope3.text = 'Scope 3 Categories Breakdown'
        
        scope3_table = ET.SubElement(scope3_div, 'table', {'class': 'scope3-table'})
        thead_s3 = ET.SubElement(scope3_table, 'thead')
        tr_header_s3 = ET.SubElement(thead_s3, 'tr')
        
        headers_s3 = ['Category', 'Emissions (tCO₂e)', 'Method', 'Data Quality', 'Coverage']
        for header in headers_s3:
            th = ET.SubElement(tr_header_s3, 'th')
            th.text = header
        
        tbody_s3 = ET.SubElement(scope3_table, 'tbody')
        
        for i in range(1, 16):
            cat_data = data['scope3_detailed'].get(f'category_{i}', {})
            tr_cat = ET.SubElement(tbody_s3, 'tr')
            
            # Category name
            td_cat_name = ET.SubElement(tr_cat, 'td')
            td_cat_name.text = f"Cat {i}: {SCOPE3_CATEGORIES[i]}"
            
            # Emissions
            td_cat_emissions = ET.SubElement(tr_cat, 'td')
            if not cat_data.get('excluded', False):
                create_enhanced_xbrl_tag(
                    td_cat_emissions,
                    'nonFraction',
                    f'esrs-e1:Scope3Category{i}',
                    f'c-cat{i}',
                    cat_data.get('emissions_tco2e', 0),
                    unit_ref='u-tCO2e',
                    decimals='0'
                )
            else:
                td_cat_emissions.text = 'Excluded'
            
            # Method
            td_cat_method = ET.SubElement(tr_cat, 'td')
            td_cat_method.text = cat_data.get('calculation_method', 'N/A')
            
            # Data quality
            td_cat_quality = ET.SubElement(tr_cat, 'td')
            if cat_data.get('data_quality_tier'):
                quality_span = ET.SubElement(td_cat_quality, 'span', {
                    'class': f'data-quality-indicator quality-{cat_data["data_quality_tier"].lower()}',
                    'data-score': str(cat_data.get('data_quality_score', 0))
                })
                quality_span.text = cat_data['data_quality_tier']
            else:
                td_cat_quality.text = 'N/A'
            
            # Coverage
            td_cat_coverage = ET.SubElement(tr_cat, 'td')
            td_cat_coverage.text = f"{cat_data.get('coverage_percent', 0)}%" if not cat_data.get('excluded') else 'N/A'
    
    # GHG intensity metrics
    if data.get('intensity'):
        intensity_div = ET.SubElement(emissions_section, 'div', {'class': 'ghg-intensity'})
        h3_intensity = ET.SubElement(intensity_div, 'h3')
        h3_intensity.text = 'GHG Intensity Metrics'
        
        if data['intensity'].get('revenue'):
            p_revenue = ET.SubElement(intensity_div, 'p')
            p_revenue.text = 'GHG intensity per revenue: '
            create_enhanced_xbrl_tag(
                p_revenue,
                'nonFraction',
                'esrs-e1:GHGIntensityRevenue',
                'c-current',
                data['intensity']['revenue'],
                unit_ref='u-tCO2e-per-EUR',
                decimals='2'
            )
            p_revenue.tail = ' tCO₂e/million EUR'

def add_removals_section(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add E1-7 GHG removals and carbon credits section"""
    removals_section = ET.SubElement(parent, 'section', {
        'class': 'removals-credits',
        'id': 'removals'
    })
    
    h2 = ET.SubElement(removals_section, 'h2')
    h2.text = 'E1-7: GHG Removals and Avoided Emissions'
    
    # GHG removals
    removals_data = data.get('removals', {})
    
    if removals_data.get('total', 0) > 0:
        removals_div = ET.SubElement(removals_section, 'div', {'class': 'ghg-removals'})
        h3_removals = ET.SubElement(removals_div, 'h3')
        h3_removals.text = 'GHG Removals'
        
        p_total = ET.SubElement(removals_div, 'p')
        p_total.text = 'Total GHG removals: '
        create_enhanced_xbrl_tag(
            p_total,
            'nonFraction',
            'esrs-e1:GHGRemovalsTotal',
            'c-current',
            removals_data['total'],
            unit_ref='u-tCO2e',
            decimals='0'
        )
        p_total.tail = ' tCO₂e'
        
        # Removals within value chain
        if removals_data.get('within_value_chain'):
            p_within = ET.SubElement(removals_div, 'p')
            p_within.text = 'Removals within value chain: '
            create_enhanced_xbrl_tag(
                p_within,
                'nonFraction',
                'esrs-e1:RemovalsWithinValueChain',
                'c-current',
                removals_data['within_value_chain'],
                unit_ref='u-tCO2e',
                decimals='0'
            )
            p_within.tail = ' tCO₂e'
        
        # Removal types
        if removals_data.get('by_type'):
            types_table = ET.SubElement(removals_div, 'table')
            thead = ET.SubElement(types_table, 'thead')
            tr_header = ET.SubElement(thead, 'tr')
            
            headers = ['Removal Type', 'Amount (tCO₂e)', 'Permanence (years)']
            for header in headers:
                th = ET.SubElement(tr_header, 'th')
                th.text = header
            
            tbody = ET.SubElement(types_table, 'tbody')
            
            for removal_type, amount in removals_data['by_type'].items():
                if amount > 0:
                    tr = ET.SubElement(tbody, 'tr')
                    
                    td_type = ET.SubElement(tr, 'td')
                    td_type.text = removal_type.replace('_', ' ').title()
                    
                    td_amount = ET.SubElement(tr, 'td')
                    td_amount.text = f"{amount:,.0f}"
                    
                    td_permanence = ET.SubElement(tr, 'td')
                    td_permanence.text = removals_data.get('permanence', {}).get(removal_type, 'TBD')
    
    # Carbon credits
    credits_data = data.get('carbon_credits', {})
    if credits_data.get('used'):
        credits_div = ET.SubElement(removals_section, 'div', {'class': 'carbon-credits'})
        h3_credits = ET.SubElement(credits_div, 'h3')
        h3_credits.text = 'Carbon Credits'
        
        p_warning = ET.SubElement(credits_div, 'p', {'class': 'credits-warning'})
        p_warning.text = '⚠️ Carbon credits are reported separately and do not reduce gross emissions'
        
        p_total_credits = ET.SubElement(credits_div, 'p')
        p_total_credits.text = 'Total carbon credits used: '
        create_enhanced_xbrl_tag(
            p_total_credits,
            'nonFraction',
            'esrs-e1:CarbonCreditsUsed',
            'c-current',
            credits_data.get('total_amount', 0),
            unit_ref='u-tCO2e',
            decimals='0'
        )
        p_total_credits.tail = ' tCO₂e'
        
        # Credits table
        if credits_data.get('credits'):
            credits_table = ET.SubElement(credits_div, 'table')
            thead = ET.SubElement(credits_table, 'thead')
            tr_header = ET.SubElement(thead, 'tr')
            
            headers = ['Type', 'Registry', 'Vintage', 'Amount (tCO₂e)', 'Purpose']
            for header in headers:
                th = ET.SubElement(tr_header, 'th')
                th.text = header
            
            tbody = ET.SubElement(credits_table, 'tbody')
            
            for credit in credits_data['credits']:
                tr = ET.SubElement(tbody, 'tr')
                
                td_type = ET.SubElement(tr, 'td')
                td_type.text = credit.get('type', 'VCS')
                
                td_registry = ET.SubElement(tr, 'td')
                td_registry.text = credit.get('registry', 'Verra')
                
                td_vintage = ET.SubElement(tr, 'td')
                td_vintage.text = str(credit.get('vintage', ''))
                
                td_amount = ET.SubElement(tr, 'td')
                td_amount.text = f"{credit.get('amount', 0):,.0f}"
                
                td_purpose = ET.SubElement(tr, 'td')
                td_purpose.text = credit.get('purpose', 'Voluntary offsetting')
        
        # Contribution claim
        if credits_data.get('contribution_claims_only'):
            p_contribution = ET.SubElement(credits_div, 'p')
            p_contribution.text = '✓ Carbon credits used for contribution claims only (not offsetting)'

def add_carbon_pricing_section_enhanced(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add E1-8 internal carbon pricing section"""
    pricing_section = ET.SubElement(parent, 'section', {
        'class': 'carbon-pricing',
        'id': 'pricing'
    })
    
    h2 = ET.SubElement(pricing_section, 'h2')
    h2.text = 'E1-8: Internal Carbon Pricing'
    
    pricing_data = data.get('carbon_pricing', {})
    
    # Implementation status
    p_implemented = ET.SubElement(pricing_section, 'p')
    p_implemented.text = 'Internal carbon pricing implemented: '
    create_enhanced_xbrl_tag(
        p_implemented,
        'nonNumeric',
        'esrs-e1:InternalCarbonPricingImplemented',
        'c-current',
        'Yes' if pricing_data.get('implemented', False) else 'No',
        xml_lang='en'
    )
    
    if pricing_data.get('implemented'):
        # Pricing details
        pricing_table = ET.SubElement(pricing_section, 'table', {'class': 'pricing-table'})
        thead = ET.SubElement(pricing_table, 'thead')
        tr_header = ET.SubElement(thead, 'tr')
        
        headers = ['Scope', 'Price (EUR/tCO₂e)', 'Application', 'Coverage %']
        for header in headers:
            th = ET.SubElement(tr_header, 'th')
            th.text = header
        
        tbody = ET.SubElement(pricing_table, 'tbody')
        
        # Shadow price
        if pricing_data.get('shadow_price_eur'):
            tr_shadow = ET.SubElement(tbody, 'tr')
            
            td_scope = ET.SubElement(tr_shadow, 'td')
            td_scope.text = 'Shadow price'
            
            td_price = ET.SubElement(tr_shadow, 'td')
            create_enhanced_xbrl_tag(
                td_price,
                'nonFraction',
                'esrs-e1:ShadowCarbonPrice',
                'c-current',
                pricing_data['shadow_price_eur'],
                unit_ref='u-EUR-per-tCO2e',
                decimals='0'
            )
            
            td_application = ET.SubElement(tr_shadow, 'td')
            td_application.text = pricing_data.get('shadow_price_application', 'Investment decisions')
            
            td_coverage = ET.SubElement(tr_shadow, 'td')
            td_coverage.text = f"{pricing_data.get('shadow_price_coverage', 0)}%"
        
        # Internal fee
        if pricing_data.get('internal_fee_eur'):
            tr_fee = ET.SubElement(tbody, 'tr')
            
            td_scope = ET.SubElement(tr_fee, 'td')
            td_scope.text = 'Internal fee'
            
            td_price = ET.SubElement(tr_fee, 'td')
            create_enhanced_xbrl_tag(
                td_price,
                'nonFraction',
                'esrs-e1:InternalCarbonFee',
                'c-current',
                pricing_data['internal_fee_eur'],
                unit_ref='u-EUR-per-tCO2e',
                decimals='0'
            )
            
            td_application = ET.SubElement(tr_fee, 'td')
            td_application.text = pricing_data.get('internal_fee_application', 'Business units')
            
            td_coverage = ET.SubElement(tr_fee, 'td')
            td_coverage.text = f"{pricing_data.get('internal_fee_coverage', 0)}%"
        
        # Total revenue/cost
        if pricing_data.get('total_revenue_eur'):
            p_revenue = ET.SubElement(pricing_section, 'p')
            p_revenue.text = 'Total carbon pricing revenue collected: €'
            create_enhanced_xbrl_tag(
                p_revenue,
                'nonFraction',
                'esrs-e1:CarbonPricingRevenue',
                'c-current',
                pricing_data['total_revenue_eur'],
                unit_ref='u-EUR',
                decimals='0'
            )
        
        # Use of proceeds
        if pricing_data.get('revenue_use'):
            use_div = ET.SubElement(pricing_section, 'div', {'class': 'revenue-use'})
            h3_use = ET.SubElement(use_div, 'h3')
            h3_use.text = 'Use of Carbon Pricing Revenue'
            
            p_use = ET.SubElement(use_div, 'p')
            create_enhanced_xbrl_tag(
                p_use,
                'nonNumeric',
                'esrs-e1:CarbonPricingRevenueUse',
                'c-current',
                pricing_data['revenue_use'],
                xml_lang='en'
            )
    
    # External carbon pricing exposure
    if pricing_data.get('eu_ets_exposure'):
        external_div = ET.SubElement(pricing_section, 'div', {'class': 'external-pricing'})
        h3_external = ET.SubElement(external_div, 'h3')
        h3_external.text = 'External Carbon Pricing Exposure'
        
        p_ets = ET.SubElement(external_div, 'p')
        p_ets.text = 'EU ETS allowances required: '
        create_enhanced_xbrl_tag(
            p_ets,
            'nonFraction',
            'esrs-e1:EUETSAllowancesRequired',
            'c-current',
            pricing_data['eu_ets_exposure'].get('allowances_required', 0),
            unit_ref='u-tCO2e',
            decimals='0'
        )
        p_ets.tail = ' tCO₂e'
        
        if pricing_data['eu_ets_exposure'].get('cost_eur'):
            p_cost = ET.SubElement(external_div, 'p')
            p_cost.text = 'EU ETS cost: €'
            create_enhanced_xbrl_tag(
                p_cost,
                'nonFraction',
                'esrs-e1:EUETSCost',
                'c-current',
                pricing_data['eu_ets_exposure']['cost_eur'],
                unit_ref='u-EUR',
                decimals='0'
            )

def add_eu_taxonomy_section(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add EU Taxonomy alignment disclosures"""
    taxonomy_section = ET.SubElement(parent, 'section', {
        'class': 'eu-taxonomy',
        'id': 'eu-taxonomy'
    })
    
    h2 = ET.SubElement(taxonomy_section, 'h2')
    h2.text = 'EU Taxonomy Alignment'
    
    taxonomy_data = data.get('eu_taxonomy_data', {})
    
    if taxonomy_data:
        # Eligibility and alignment overview
        overview_div = ET.SubElement(taxonomy_section, 'div', {'class': 'taxonomy-overview'})
        
        # KPIs
        kpi_grid = ET.SubElement(overview_div, 'div', {'class': 'kpi-grid'})
        
        kpis = [
            ('Revenue', taxonomy_data.get('revenue_aligned_percent', 0), 'revenue'),
            ('CapEx', taxonomy_data.get('capex_aligned_percent', 0), 'capex'),
            ('OpEx', taxonomy_data.get('opex_aligned_percent', 0), 'opex')
        ]
        
        for kpi_name, value, kpi_type in kpis:
            kpi_card = ET.SubElement(kpi_grid, 'div', {'class': 'kpi-card'})
            
            label_div = ET.SubElement(kpi_card, 'div', {'class': 'kpi-label'})
            label_div.text = f'Taxonomy-aligned {kpi_name}'
            
            value_div = ET.SubElement(kpi_card, 'div', {'class': 'kpi-value'})
            create_enhanced_xbrl_tag(
                value_div,
                'nonFraction',
                f'eu-tax:TaxonomyAligned{kpi_name.replace(" ", "")}Percentage',
                'c-current',
                value,
                unit_ref='u-percent',
                decimals='1'
            )
            
            unit_div = ET.SubElement(kpi_card, 'div', {'class': 'kpi-unit'})
            unit_div.text = '%'
        
        # Eligible activities
        if taxonomy_data.get('eligible_activities'):
            activities_div = ET.SubElement(taxonomy_section, 'div', {'class': 'eligible-activities'})
            h3_activities = ET.SubElement(activities_div, 'h3')
            h3_activities.text = 'Taxonomy-Eligible Activities'
            
            activities_table = ET.SubElement(activities_div, 'table')
            thead = ET.SubElement(activities_table, 'thead')
            tr_header = ET.SubElement(thead, 'tr')
            
            headers = ['Activity', 'NACE Code', 'Revenue %', 'CapEx %', 'Aligned']
            for header in headers:
                th = ET.SubElement(tr_header, 'th')
                th.text = header
            
            tbody = ET.SubElement(activities_table, 'tbody')
            
            for activity in taxonomy_data['eligible_activities']:
                tr = ET.SubElement(tbody, 'tr')
                
                td_name = ET.SubElement(tr, 'td')
                td_name.text = activity['name']
                
                td_nace = ET.SubElement(tr, 'td')
                td_nace.text = activity.get('nace_code', '')
                
                td_revenue = ET.SubElement(tr, 'td')
                td_revenue.text = f"{activity.get('revenue_percent', 0)}%"
                
                td_capex = ET.SubElement(tr, 'td')
                td_capex.text = f"{activity.get('capex_percent', 0)}%"
                
                td_aligned = ET.SubElement(tr, 'td')
                td_aligned.text = '✓' if activity.get('aligned', False) else '✗'
        
        # DNSH criteria
        if taxonomy_data.get('dnsh_assessments'):
            dnsh_div = ET.SubElement(taxonomy_section, 'div', {'class': 'dnsh-criteria'})
            h3_dnsh = ET.SubElement(dnsh_div, 'h3')
            h3_dnsh.text = 'Do No Significant Harm (DNSH) Criteria'
            
            dnsh_table = ET.SubElement(dnsh_div, 'table', {'class': 'dnsh-criteria'})
            thead = ET.SubElement(dnsh_table, 'thead')
            tr_header = ET.SubElement(thead, 'tr')
            
            headers = ['Environmental Objective', 'Compliant', 'Evidence']
            for header in headers:
                th = ET.SubElement(tr_header, 'th')
                th.text = header
            
            tbody = ET.SubElement(dnsh_table, 'tbody')
            
            dnsh_objectives = [
                'Climate change mitigation',
                'Climate change adaptation',
                'Water and marine resources',
                'Circular economy',
                'Pollution prevention',
                'Biodiversity and ecosystems'
            ]
            
            for objective in dnsh_objectives:
                obj_key = objective.lower().replace(' ', '_')
                assessment = taxonomy_data['dnsh_assessments'].get(obj_key, {})
                
                tr = ET.SubElement(tbody, 'tr')
                
                td_objective = ET.SubElement(tr, 'td')
                td_objective.text = objective
                
                td_compliant = ET.SubElement(tr, 'td')
                td_compliant.text = 'Yes' if assessment.get('compliant', False) else 'No'
                
                td_evidence = ET.SubElement(tr, 'td')
                td_evidence.text = assessment.get('evidence_summary', 'See documentation')
    else:
        p = ET.SubElement(taxonomy_section, 'p')
        p.text = 'EU Taxonomy assessment pending completion.'

def add_value_chain_section(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add value chain engagement section"""
    vc_section = ET.SubElement(parent, 'section', {
        'class': 'value-chain',
        'id': 'value-chain'
    })
    
    h2 = ET.SubElement(vc_section, 'h2')
    h2.text = 'Value Chain Engagement'
    
    # Upstream value chain
    upstream_div = ET.SubElement(vc_section, 'div', {'class': 'upstream-value-chain'})
    h3_upstream = ET.SubElement(upstream_div, 'h3')
    h3_upstream.text = 'Upstream Value Chain'
    
    if data.get('value_chain', {}).get('upstream'):
        upstream_data = data['value_chain']['upstream']
        
        # Supplier engagement
        p_suppliers = ET.SubElement(upstream_div, 'p')
        p_suppliers.text = 'Suppliers with climate targets: '
        create_enhanced_xbrl_tag(
            p_suppliers,
            'nonFraction',
            'esrs-e1:SuppliersWithClimateTargetsPercentage',
            'c-value-chain-upstream',
            upstream_data.get('suppliers_with_targets_percent', 0),
            unit_ref='u-percent',
            decimals='1',
            assurance_status='reviewed'
        )
        p_suppliers.tail = '%'
        
        # Supplier engagement program
        if upstream_data.get('engagement_program'):
            engagement_p = ET.SubElement(upstream_div, 'p')
            engagement_p.text = 'Supplier engagement program: '
            create_enhanced_xbrl_tag(
                engagement_p,
                'nonNumeric',
                'esrs-e1:SupplierEngagementProgram',
                'c-current',
                upstream_data['engagement_program'],
                xml_lang='en'
            )
    
    # Own operations
    own_div = ET.SubElement(vc_section, 'div', {'class': 'own-operations'})
    h3_own = ET.SubElement(own_div, 'h3')
    h3_own.text = 'Own Operations'
    
    p_own = ET.SubElement(own_div, 'p')
    p_own.text = 'See emissions data in E1-6 section for detailed breakdown of own operations.'
    
    # Downstream value chain
    downstream_div = ET.SubElement(vc_section, 'div', {'class': 'downstream'})
    h3_down = ET.SubElement(downstream_div, 'h3')
    h3_down.text = 'Downstream Value Chain'
    
    if data.get('value_chain', {}).get('downstream'):
        downstream_data = data['value_chain']['downstream']
        
        # Product carbon footprint
        if downstream_data.get('product_carbon_footprints'):
            pcf_p = ET.SubElement(downstream_div, 'p')
            pcf_p.text = 'Product carbon footprint assessments completed: '
            create_enhanced_xbrl_tag(
                pcf_p,
                'nonNumeric',
                'esrs-e1:ProductCarbonFootprintAssessments',
                'c-current',
                'Yes',
                xml_lang='en'
            )
            
            # PCF table
            pcf_table = ET.SubElement(downstream_div, 'table', {'class': 'pcf-table'})
            thead = ET.SubElement(pcf_table, 'thead')
            tr_header = ET.SubElement(thead, 'tr')
            
            headers = ['Product', 'Carbon Footprint (kgCO₂e/unit)', 'LCA Standard', 'Coverage']
            for header in headers:
                th = ET.SubElement(tr_header, 'th')
                th.text = header
            
            tbody = ET.SubElement(pcf_table, 'tbody')
            
            for idx, pcf in enumerate(downstream_data['product_carbon_footprints']):
                tr = ET.SubElement(tbody, 'tr')
                
                td_product = ET.SubElement(tr, 'td')
                td_product.text = pcf['product_name']
                
                td_footprint = ET.SubElement(tr, 'td')
                create_enhanced_xbrl_tag(
                    td_footprint,
                    'nonFraction',
                    f'esrs-e1:ProductCarbonFootprint{idx+1}',
                    'c-downstream',
                    pcf['carbon_footprint_kg'],
                    unit_ref='u-kgCO2e-per-unit',
                    decimals='1'
                )
                
                td_standard = ET.SubElement(tr, 'td')
                td_standard.text = pcf.get('lca_standard', 'ISO 14067')
                
                td_coverage = ET.SubElement(tr, 'td')
                td_coverage.text = pcf.get('lifecycle_coverage', 'Cradle-to-gate')

def add_methodology_section(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add methodology section"""
    method_section = ET.SubElement(parent, 'section', {
        'class': 'methodology',
        'id': 'methodology'
    })
    
    h2 = ET.SubElement(method_section, 'h2')
    h2.text = 'Methodology and Data Quality'
    
    # Calculation methodology
    calc_div = ET.SubElement(method_section, 'div', {'class': 'calculation-methodology'})
    h3_calc = ET.SubElement(calc_div, 'h3')
    h3_calc.text = 'Calculation Methodology'
    
    p_standard = ET.SubElement(calc_div, 'p')
    p_standard.text = 'GHG accounting standard: '
    create_enhanced_xbrl_tag(
        p_standard,
        'nonNumeric',
        'esrs-e1:GHGAccountingStandard',
        'c-current',
        data.get('methodology', {}).get('ghg_standard', 'GHG Protocol Corporate Standard'),
        xml_lang='en'
    )
    
    # Consolidation approach
    p_consolidation = ET.SubElement(calc_div, 'p')
    p_consolidation.text = 'Consolidation approach: '
    create_enhanced_xbrl_tag(
        p_consolidation,
        'nonNumeric',
        'esrs-e1:ConsolidationApproach',
        'c-current',
        data.get('methodology', {}).get('consolidation_approach', 'Operational control'),
        xml_lang='en'
    )
    
    # Emission factors
    ef_div = ET.SubElement(method_section, 'div', {'class': 'emission-factors'})
    h3_ef = ET.SubElement(ef_div, 'h3')
    h3_ef.text = 'Emission Factor Sources'
    
    ef_sources = data.get('methodology', {}).get('emission_factor_sources', [
        'DEFRA 2024',
        'IEA Electricity Factors 2024',
        'EPA Emission Factors Hub'
    ])
    
    ul_ef = ET.SubElement(ef_div, 'ul')
    for source in ef_sources:
        li = ET.SubElement(ul_ef, 'li')
        li.text = source
    
    # Data quality assessment
    quality_div = ET.SubElement(method_section, 'div', {'class': 'data-quality'})
    h3_quality = ET.SubElement(quality_div, 'h3')
    h3_quality.text = 'Data Quality Assessment'
    
    p_quality = ET.SubElement(quality_div, 'p')
    p_quality.text = 'Average data quality score across all Scope 3 categories: '
    create_enhanced_xbrl_tag(
        p_quality,
        'nonFraction',
        'esrs-e1:AverageDataQualityScore',
        'c-current',
        data.get('data_quality_score', 0),
        decimals='0'
    )
    p_quality.tail = '/100'
    
    # Uncertainty assessment
    if data.get('uncertainty_assessment'):
        uncertainty_div = ET.SubElement(method_section, 'div', {'class': 'uncertainty'})
        h3_uncertainty = ET.SubElement(uncertainty_div, 'h3')
        h3_uncertainty.text = 'Uncertainty Assessment'
        
        p_uncertainty = ET.SubElement(uncertainty_div, 'p')
        create_enhanced_xbrl_tag(
            p_uncertainty,
            'nonNumeric',
            'esrs-e1:UncertaintyAssessment',
            'c-current',
            data['uncertainty_assessment'],
            xml_lang='en'
        )
    
    # Recalculation policy
    if data.get('recalculation_policy'):
        recalc_div = ET.SubElement(method_section, 'div', {'class': 'recalculation-policy'})
        h3_recalc = ET.SubElement(recalc_div, 'h3')
        h3_recalc.text = 'Base Year Recalculation Policy'
        
        p_recalc = ET.SubElement(recalc_div, 'p')
        create_enhanced_xbrl_tag(
            p_recalc,
            'nonNumeric',
            'esrs-e1:RecalculationPolicy',
            'c-current',
            data['recalculation_policy'],
            xml_lang='en'
        )

def add_assurance_section(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add assurance section"""
    assurance_section = ET.SubElement(parent, 'section', {
        'class': 'assurance',
        'id': 'assurance'
    })
    
    h2 = ET.SubElement(assurance_section, 'h2')
    h2.text = 'Assurance'
    
    assurance_data = data.get('assurance', {})
    
    if assurance_data:
        # Assurance statement
        statement_div = ET.SubElement(assurance_section, 'div', {'class': 'assurance-statement'})
        
        p_level = ET.SubElement(statement_div, 'p')
        p_level.text = 'Level of assurance: '
        create_enhanced_xbrl_tag(
            p_level,
            'nonNumeric',
            'esrs-e1:AssuranceLevel',
            'c-current',
            assurance_data.get('level', 'Limited assurance'),
            xml_lang='en'
        )
        
        p_provider = ET.SubElement(statement_div, 'p')
        p_provider.text = 'Assurance provider: '
        create_enhanced_xbrl_tag(
            p_provider,
            'nonNumeric',
            'esrs-e1:AssuranceProvider',
            'c-current',
            assurance_data.get('provider', 'TBD'),
            xml_lang='en'
        )
        
        p_standard = ET.SubElement(statement_div, 'p')
        p_standard.text = 'Assurance standard: '
        create_enhanced_xbrl_tag(
            p_standard,
            'nonNumeric',
            'esrs-e1:AssuranceStandard',
            'c-current',
            assurance_data.get('standard', 'ISAE 3410'),
            xml_lang='en'
        )
        
        # Scope of assurance
        if assurance_data.get('scope'):
            scope_div = ET.SubElement(statement_div, 'div', {'class': 'assurance-scope'})
            h3_scope = ET.SubElement(scope_div, 'h3')
            h3_scope.text = 'Scope of Assurance'
            
            ul_scope = ET.SubElement(scope_div, 'ul')
            for item in assurance_data['scope']:
                li = ET.SubElement(ul_scope, 'li')
                li.text = item
        
        # Link to assurance report
        if assurance_data.get('report_link'):
            p_link = ET.SubElement(statement_div, 'p')
            p_link.text = 'Full assurance report available at: '
            a_link = ET.SubElement(p_link, 'a', {'href': assurance_data['report_link']})
            a_link.text = assurance_data['report_link']
    else:
        p = ET.SubElement(assurance_section, 'p')
        p.text = 'This report has not yet been subject to external assurance. Assurance is planned for the next reporting cycle.'

def add_change_tracking(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add change tracking section for amendments"""
    if not data.get('amendments'):
        return
    
    changes_section = ET.SubElement(parent, 'section', {
        'class': 'change-tracking',
        'id': 'changes'
    })
    
    h2 = ET.SubElement(changes_section, 'h2')
    h2.text = 'Amendments and Restatements'
    
    amendments_table = ET.SubElement(changes_section, 'table')
    thead = ET.SubElement(amendments_table, 'thead')
    tr_header = ET.SubElement(thead, 'tr')
    
    headers = ['Date', 'Section', 'Description', 'Reason', 'Impact']
    for header in headers:
        th = ET.SubElement(tr_header, 'th')
        th.text = header
    
    tbody = ET.SubElement(amendments_table, 'tbody')
    
    for amendment in data['amendments']:
        tr = ET.SubElement(tbody, 'tr')
        
        td_date = ET.SubElement(tr, 'td')
        td_date.text = amendment['date']
        
        td_section = ET.SubElement(tr, 'td')
        td_section.text = amendment['section']
        
        td_desc = ET.SubElement(tr, 'td')
        td_desc.text = amendment['description']
        
        td_reason = ET.SubElement(tr, 'td')
        td_reason.text = amendment['reason']
        
        td_impact = ET.SubElement(tr, 'td')
        td_impact.text = amendment.get('impact', 'None')

def add_evidence_packaging(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add evidence packaging references"""
    if not data.get('evidence_packages'):
        return
    
    evidence_section = ET.SubElement(parent, 'section', {
        'class': 'evidence-packages',
        'id': 'evidence'
    })
    
    h2 = ET.SubElement(evidence_section, 'h2')
    h2.text = 'Evidence Documentation'
    
    evidence_table = ET.SubElement(evidence_section, 'table')
    thead = ET.SubElement(evidence_table, 'thead')
    tr_header = ET.SubElement(thead, 'tr')
    
    headers = ['Reference', 'Data Point', 'Document Type', 'Location']
    for header in headers:
        th = ET.SubElement(tr_header, 'th')
        th.text = header
    
    tbody = ET.SubElement(evidence_table, 'tbody')
    
    for package in data['evidence_packages']:
        tr = ET.SubElement(tbody, 'tr')
        
        td_ref = ET.SubElement(tr, 'td')
        td_ref.text = package['reference']
        
        td_datapoint = ET.SubElement(tr, 'td')
        td_datapoint.text = package['data_point']
        
        td_type = ET.SubElement(tr, 'td')
        td_type.text = package['document_type']
        
        td_location = ET.SubElement(tr, 'td')
        td_location.text = package.get('location', 'Available on request')

def add_sme_simplifications(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add SME simplifications section if applicable"""
    if data.get('company_size') not in ['small', 'medium']:
        return
    
    sme_section = ET.SubElement(parent, 'section', {
        'class': 'sme-simplifications',
        'id': 'sme'
    })
    
    h2 = ET.SubElement(sme_section, 'h2')
    h2.text = 'SME Simplifications Applied'
    
    p = ET.SubElement(sme_section, 'p')
    p.text = f'As a {data["company_size"]} enterprise, the following simplifications have been applied in accordance with ESRS proportionality provisions:'
    
    simplifications = data.get('sme_simplifications', [])
    if simplifications:
        ul = ET.SubElement(sme_section, 'ul')
        for simplification in simplifications:
            li = ET.SubElement(ul, 'li')
            li.text = simplification

def add_document_versioning(parent: ET.Element, data: Dict[str, Any]) -> None:
    """Add document version control information"""
    version_section = ET.SubElement(parent, 'section', {
        'class': 'document-versioning',
        'id': 'versioning'
    })
    
    h2 = ET.SubElement(version_section, 'h2')
    h2.text = 'Document Version Control'
    
    version_table = ET.SubElement(version_section, 'table')
    tbody = ET.SubElement(version_table, 'tbody')
    
    version_info = [
        ('Document Version', data.get('document_version', '1.0')),
        ('Generation Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('XBRL Taxonomy Version', data.get('taxonomy_version', 'EFRAG 2024.1.0')),
        ('Generator Version', '2.0 Enhanced'),
        ('Last Modified', data.get('last_modified', datetime.now().isoformat()))
    ]
    
    for label, value in version_info:
        tr = ET.SubElement(tbody, 'tr')
        
        td_label = ET.SubElement(tr, 'td')
        td_label.text = label
        
        td_value = ET.SubElement(tr, 'td')
        td_value.text = value

# Helper function that should be imported or defined
def create_enhanced_xbrl_tag(
    parent: ET.Element,
    tag_type: str,
    name: str,
    context_ref: str,
    value: Any,
    unit_ref: str = None,
    decimals: str = None,
    xml_lang: str = None,
    assurance_status: str = None,
    format: str = None,
    **kwargs
) -> ET.Element:
    """Create XBRL tag with all required attributes"""
    
    namespace = '{http://www.xbrl.org/2013/inlineXBRL}'
    tag = ET.SubElement(parent, f'{namespace}{tag_type}', {
        'name': name,
        'contextRef': context_ref
    })
    
    if unit_ref:
        tag.set('unitRef', unit_ref)
    
    if decimals is not None:
        tag.set('decimals', str(decimals))
    
    if xml_lang:
        tag.set('{http://www.w3.org/XML/1998/namespace}lang', xml_lang)
    elif tag_type == 'nonNumeric':
        tag.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')
    
    if format:
        tag.set('format', format)
    
    if assurance_status:
        tag.set('data-assurance-status', assurance_status)
    
    # Set the value
    if isinstance(value, (int, float)) and tag_type == 'nonFraction':
        tag.text = f"{value:.{int(decimals) if decimals else 0}f}"
    elif value is None:
        tag.set('{http://www.w3.org/2001/XMLSchema-instance}nil', 'true')
        tag.text = ""
    else:
        tag.text = str(value)
    
    return tag

def calculate_percentage_change(previous: float, current: float) -> float:
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def generate_qualified_signature(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate qualified electronic signature metadata"""
    return {
        'signature_type': 'Qualified Electronic Signature',
        'signature_time': datetime.now().isoformat(),
        'signer_certificate': {
            'subject': data.get('authorized_representative', 'CFO'),
            'issuer': 'Qualified Trust Service Provider',
            'validity': 'Valid'
        },
        'signature_value': 'SIGNATURE_PLACEHOLDER',
        'signature_properties': {
            'reason': 'ESRS E1 Report Approval',
            'location': data.get('headquarters_location', 'EU'),
            'commitment_type': 'ProofOfApproval'
        }
    }

