"""
Water Quality Analysis Utility
Provides analysis and interpretation of water quality parameters
"""

# Define safety thresholds for different parameters
# These values are based on common guidelines but should be verified for your specific context
THRESHOLDS = {
    # Parameter: [min_human, max_human, min_fish, max_fish]
    "ph": [6.5, 8.5, 6.0, 9.0],  # pH safe range for humans and fish
    "bod": [None, 5, None, 6],  # BOD in mg/l
    "cod": [None, 10, None, 20],  # COD in mg/l
    "temperature": [None, 30, 10, 25],  # Temperature in °C
    "ammonia": [None, 1.5, None, 0.05],  # Ammonia in mg/l
    "arsenic": [None, 0.01, None, 0.05],  # Arsenic in mg/l
    "calcium": [None, 200, None, 100],  # Calcium in mg/l
    "ec": [None, 1500, None, 1000],  # EC (μS/cm)
    "coliform": [None, 0, None, 200],  # Coliform (N/100ml)
    "hardness": [None, 300, None, 150],  # Hardness in mg/l
    "lead_pb": [None, 0.015, None, 0.03],  # Lead in mg/l
    "nitrogen": [None, 10, None, 3],  # Nitrogen in mg/l
    "sodium": [None, 200, None, 100],  # Sodium in mg/l
    "sulfate": [None, 250, None, 100],  # Sulfate in mg/l
    "tss": [None, 50, None, 25],  # TSS in mg/l
    "turbidity": [None, 5, None, 10],  # Turbidity in NTU
    "tds": [None, 500, None, 400],  # TDS in mg/l
}

# Parameter descriptions for explanation
PARAMETER_DESCRIPTIONS = {
    "ph": "pH measures how acidic or basic the water is. Extreme values can harm aquatic life and make water unsafe for human use.",
    "bod": "Biochemical Oxygen Demand indicates organic pollution. High values suggest contamination from waste or organic matter.",
    "cod": "Chemical Oxygen Demand measures the amount of oxygen required to oxidize all compounds in water. Higher values indicate pollution.",
    "temperature": "Water temperature affects oxygen levels and aquatic life. High temperatures can stress fish and promote bacterial growth.",
    "ammonia": "Ammonia can be toxic to fish even at low concentrations. It often comes from waste decomposition.",
    "arsenic": "A toxic heavy metal that can cause serious health problems in humans and aquatic life.",
    "calcium": "Essential mineral for aquatic life, but excessive amounts can contribute to water hardness problems.",
    "ec": "Electrical Conductivity measures dissolved salts. High values may indicate pollution or salt water intrusion.",
    "coliform": "Indicates potential fecal contamination and disease-causing organisms.",
    "hardness": "Measures calcium and magnesium content. Very hard water can cause scaling, while soft water may be corrosive.",
    "lead_pb": "Toxic heavy metal that can cause developmental issues in humans and harm aquatic life.",
    "nitrogen": "Essential nutrient that in excess can cause algae blooms and oxygen depletion.",
    "sodium": "High sodium levels may affect people with hypertension and can harm some freshwater organisms.",
    "sulfate": "High levels can give water a bitter taste and may have laxative effects.",
    "tss": "Total Suspended Solids reduce water clarity and can harm aquatic ecosystems.",
    "turbidity": "Measures water cloudiness. High turbidity can harbor pathogens and reduce light penetration for aquatic plants.",
    "tds": "Total Dissolved Solids include minerals, salts, and metals dissolved in water."
}

def generate_analysis_text(param_name, value, analysis_result):
    """Generate detailed textual analysis for a parameter"""
    if value is None or value == "":
        return "No data provided for this parameter."
        
    try:
        value = float(value)
        thresholds = THRESHOLDS.get(param_name)
        description = PARAMETER_DESCRIPTIONS.get(param_name, "No description available.")
        
        if not thresholds:
            return f"{description} No specific thresholds available for analysis."
            
        min_human, max_human, min_fish, max_fish = thresholds
        human_safe = analysis_result.get("human_safe")
        fish_safe = analysis_result.get("fish_safe")
        
        result = f"{description} "
        
        # Add value assessment
        if param_name == "ph":
            if value < 7:
                result += f"The measured value ({value}) is acidic. "
            elif value > 7:
                result += f"The measured value ({value}) is alkaline. "
            else:
                result += f"The measured value ({value}) is neutral. "
        else:
            if min_human is not None and max_human is not None:
                result += f"For human safety, values should be between {min_human} and {max_human}. "
            elif max_human is not None:
                result += f"For human safety, values should be below {max_human}. "
                
            if min_fish is not None and max_fish is not None:
                result += f"For aquatic life, values should be between {min_fish} and {max_fish}. "
            elif max_fish is not None:
                result += f"For aquatic life, values should be below {max_fish}. "
        
        # Add safety assessment
        if human_safe is True and fish_safe is True:
            result += f"The current value ({value}) is within safe limits for both humans and aquatic life."
        elif human_safe is True:
            result += f"The current value ({value}) is safe for humans but may affect aquatic life."
        elif fish_safe is True:
            result += f"The current value ({value}) is safe for aquatic life but may pose risks for humans."
        else:
            result += f"The current value ({value}) exceeds recommended limits for both humans and aquatic life."
            
        # Add specific implications
        if param_name == "bod" and value > max_human:
            result += " High BOD indicates significant organic pollution, possibly from sewage or agricultural runoff."
        elif param_name == "cod" and value > max_human:
            result += " Elevated COD suggests industrial pollution or chemical contamination."
        elif param_name == "ammonia" and value > max_fish:
            result += " These ammonia levels can be lethal to fish and indicate recent contamination with organic waste."
        elif param_name == "coliform" and value > 0:
            result += " The presence of coliform bacteria indicates potential fecal contamination and health risks."
        elif param_name == "arsenic" and value > max_human:
            result += " These arsenic levels pose significant health risks with long-term exposure."
        elif param_name == "lead_pb" and value > max_human:
            result += " Lead at these levels can cause serious health problems, especially in children."
            
        return result
        
    except:
        return f"Error analyzing this parameter. {PARAMETER_DESCRIPTIONS.get(param_name, '')}"

def analyze_parameter(param_name, value):
    """Analyze a single water parameter against established thresholds"""
    if value is None or value == "":
        return {
            "human_safe": None,
            "fish_safe": None,
            "concerns": [],
            "description": PARAMETER_DESCRIPTIONS.get(param_name, "No description available.")
        }
    
    try:
        value = float(value)
        thresholds = THRESHOLDS.get(param_name)
        
        if not thresholds:
            return {
                "human_safe": None,
                "fish_safe": None,
                "concerns": [],
                "description": PARAMETER_DESCRIPTIONS.get(param_name, "No description available.")
            }
        
        min_human, max_human, min_fish, max_fish = thresholds
        concerns = []
        
        # Check for humans
        human_safe = True
        if min_human is not None and value < min_human:
            human_safe = False
            concerns.append(f"{param_name.upper()} is too low for human safety")
        if max_human is not None and value > max_human:
            human_safe = False
            concerns.append(f"{param_name.upper()} is too high for human safety")
            
        # Check for fish
        fish_safe = True
        if min_fish is not None and value < min_fish:
            fish_safe = False
            concerns.append(f"{param_name.upper()} is too low for fish safety")
        if max_fish is not None and value > max_fish:
            fish_safe = False
            concerns.append(f"{param_name.upper()} is too high for fish safety")
            
        result = {
            "human_safe": human_safe,
            "fish_safe": fish_safe,
            "concerns": concerns,
            "description": PARAMETER_DESCRIPTIONS.get(param_name, "No description available.")
        }
        
        # Add status classification
        if human_safe and fish_safe:
            result["status"] = "Good"
        else:
            result["status"] = "Concern"
            
        return result
    except:
        return {
            "human_safe": None,
            "fish_safe": None,
            "concerns": ["Error analyzing this parameter"],
            "description": PARAMETER_DESCRIPTIONS.get(param_name, "No description available."),
            "status": "Unknown"
        }

def analyze_water_quality(water_data):
    """
    Analyze water quality parameters and generate a summary
    
    Args:
        water_data: Dictionary with water quality parameters
        
    Returns:
        Dictionary with analysis results
    """
    # Clean and convert data
    clean_data = {}
    for key, value in water_data.items():
        if key in THRESHOLDS and value not in (None, ""):
            try:
                clean_data[key] = float(value)
            except:
                clean_data[key] = None
    
    # Analyze each parameter
    parameter_analysis = {}
    for param, value in clean_data.items():
        parameter_analysis[param] = analyze_parameter(param, value)
    
    # Generate detailed analysis text for each parameter
    detailed_analysis = {}
    for param, value in clean_data.items():
        detailed_analysis[f"{param}_analysis"] = generate_analysis_text(param, value, parameter_analysis[param])
        detailed_analysis[f"{param}_status"] = parameter_analysis[param].get("status", "Unknown")
    
    # Count safety issues
    human_concerns = []
    fish_concerns = []
    
    for param, analysis in parameter_analysis.items():
        if analysis['human_safe'] is False:
            human_concerns.append(f"{param} ({clean_data[param]})")
        if analysis['fish_safe'] is False:
            fish_concerns.append(f"{param} ({clean_data[param]})")
    
    # Generate overall status
    human_safe = len(human_concerns) == 0
    fish_safe = len(fish_concerns) == 0
    
    # Calculate statistics
    total_params = len(clean_data)
    human_safe_params = sum(1 for param, analysis in parameter_analysis.items() 
                           if analysis.get('human_safe') is True)
    fish_safe_params = sum(1 for param, analysis in parameter_analysis.items() 
                          if analysis.get('fish_safe') is True)
    
    # Set overall quality classification
    if human_safe and fish_safe:
        overall_quality = "Good"
        severity = "Low"
    elif len(human_concerns) > 3 or len(fish_concerns) > 3:
        overall_quality = "Poor"
        severity = "High"
    else:
        overall_quality = "Concern"
        severity = "Moderate"
    
    # Generate enhanced summary text
    summary = []
    
    # Overall quality statement
    if human_safe and fish_safe:
        summary.append(f"Water Quality Assessment: GOOD. This water appears to be safe for both humans and aquatic life based on the {total_params} parameters analyzed.")
    elif human_safe:
        summary.append(f"Water Quality Assessment: MODERATE CONCERN. This water appears to be safe for human activities but shows {len(fish_concerns)} parameters of concern for aquatic life.")
    elif fish_safe:
        summary.append(f"Water Quality Assessment: MODERATE CONCERN. This water appears to be safe for aquatic life but shows {len(human_concerns)} parameters of concern for human activities.")
    else:
        summary.append(f"Water Quality Assessment: HIGH CONCERN. This water shows concerning levels for both human use ({len(human_concerns)} parameters) and aquatic life ({len(fish_concerns)} parameters).")
    
    # Add statistics
    summary.append(f"Analysis Statistics: {human_safe_params} of {total_params} parameters are within safe limits for humans ({human_safe_params/total_params*100:.1f}%). "
                  f"{fish_safe_params} of {total_params} parameters are within safe limits for aquatic life ({fish_safe_params/total_params*100:.1f}%).")
    
    # Add specific concerns
    if human_concerns:
        summary.append(f"Parameters of concern for humans: {', '.join(human_concerns)}.")
    if fish_concerns:
        summary.append(f"Parameters of concern for aquatic life: {', '.join(fish_concerns)}.")
    
    # Add potential sources of contamination based on problematic parameters
    contamination_sources = []
    if any(param in human_concerns or param in fish_concerns for param in ["bod", "cod", "ammonia"]):
        contamination_sources.append("organic waste (possibly sewage or agricultural runoff)")
    if any(param in human_concerns or param in fish_concerns for param in ["arsenic", "lead_pb"]):
        contamination_sources.append("industrial contamination or mining activities")
    if any(param in human_concerns or param in fish_concerns for param in ["coliform"]):
        contamination_sources.append("fecal contamination")
    if any(param in human_concerns or param in fish_concerns for param in ["nitrogen"]):
        contamination_sources.append("agricultural fertilizers")
    if any(param in human_concerns or param in fish_concerns for param in ["ec", "tds", "sodium"]):
        contamination_sources.append("salt water intrusion or road salt")
    
    if contamination_sources:
        summary.append(f"Potential sources of contamination based on parameter analysis: {', '.join(contamination_sources)}.")
    
    # Add context and limitations
    summary.append("Note: This analysis is based on general guidelines and should not replace professional water quality assessment.")
    
    # Add severity assessment
    summary.append(f"Overall severity: {severity}. " + {
        "Low": "No immediate action required, routine monitoring recommended.",
        "Moderate": "Some remedial actions should be considered for problematic parameters.",
        "High": "Immediate attention required to address water quality issues."
    }[severity])
    
    # Generate recommendations
    recommendations = []
    if not human_safe:
        if severity == "High":
            recommendations.append("Avoid water contact or consumption until treatment is implemented.")
        else:
            recommendations.append("Consider water treatment or filtration before human contact or consumption.")
    
    if not fish_safe:
        if severity == "High":
            recommendations.append("This water requires immediate remediation to support aquatic life.")
        else:
            recommendations.append("This water may need remediation to better support aquatic life.")
    
    if len(human_concerns) > 3 or len(fish_concerns) > 3:
        recommendations.append("Multiple concerning parameters suggest significant contamination - investigate pollution sources and implement remediation strategies.")
    
    # Add specific parameter-based recommendations
    if any(param in human_concerns or param in fish_concerns for param in ["coliform"]):
        recommendations.append("Disinfection is recommended to eliminate potential pathogenic microorganisms.")
    
    if any(param in human_concerns or param in fish_concerns for param in ["lead_pb", "arsenic"]):
        recommendations.append("Heavy metal contamination detected - specialized filtration or treatment is required.")
    
    if any(param in human_concerns or param in fish_concerns for param in ["turbidity", "tss"]):
        recommendations.append("Filtration recommended to reduce suspended solids.")
    
    # Merge parameter analysis into final result
    result = {
        "summary": " ".join(summary),
        "human_safe": human_safe,
        "fish_safe": fish_safe,
        "human_concerns": human_concerns,
        "fish_concerns": fish_concerns,
        "recommendations": recommendations,
        "parameter_analysis": parameter_analysis,
        "analyzed_parameters": len(clean_data),
        "overall_quality": overall_quality,
        "severity": severity
    }
    
    # Add detailed analysis text for each parameter
    result.update(detailed_analysis)
    
    return result 