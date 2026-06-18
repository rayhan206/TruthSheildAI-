def build_report(scan_id, input_text, features, ml_result, dl_result, rag_context, file_meta):
    lines = [
        f"# TruthShield Lite Risk Report",
        "",
        f"Scan ID: `{scan_id}`",
        "",
        "## Verdict",
        "",
        f"- Text risk: **{ml_result['risk_level']}** ({ml_result['risk_score']}/100)",
        f"- Visual/file risk: **{dl_result['visual_risk_level']}** ({dl_result['visual_risk_score']}/100)",
        f"- Media detector: `{dl_result.get('detector_mode', 'not-applicable')}`",
        f"- Media model: `{dl_result.get('model_name', 'Not analyzed')}`",
        "",
        "## Key Reasons",
        "",
    ]

    for reason in ml_result["top_reasons"]:
        lines.append(f"- {reason}")
    for signal in dl_result["signals"]:
        lines.append(f"- {signal}")

    content_analysis = dl_result.get("content_analysis") or {}
    if content_analysis.get("available"):
        lines.extend([
            "",
            "## Frame Analysis",
            "",
            f"- Sampled frames: {content_analysis['sampled_frames']}",
            f"- Average frame AI likelihood: {content_analysis['average_frame_score']}%",
            f"- Suspicious frame ratio: {content_analysis['suspicious_frame_ratio']}%",
        ])

    lines.extend([
        "",
        "## Extracted Signals",
        "",
        f"- URLs found: {features['url_count']}",
        f"- Suspicious URLs: {features['suspicious_url_count']}",
        f"- Phone numbers: {features['phone_count']}",
        f"- Money mentions: {features['money_mention_count']}",
        f"- Urgency terms: {', '.join(features['urgency_terms']) or 'None'}",
        f"- Money terms: {', '.join(features['money_terms']) or 'None'}",
        "",
        "## Retrieved Safety Context",
        "",
    ])

    for context in rag_context:
        lines.extend([
            f"### {context['title']}",
            context["description"],
            "",
            "Signals:",
        ])
        for signal in context["signals"]:
            lines.append(f"- {signal}")
        lines.extend([
            "",
            f"Recommended action: {context['recommended_action']}",
            "",
        ])

    if file_meta:
        lines.extend([
            "## Uploaded File",
            "",
            f"- Name: `{file_meta['name']}`",
            f"- Size: {file_meta['size_bytes']} bytes",
            "",
        ])

    lines.extend([
        "## Safe Next Steps",
        "",
        "- Do not click links until the sender is verified.",
        "- Do not pay fees or deposits based only on this message.",
        "- Verify through official websites, known phone numbers, or trusted contacts.",
        "- Preserve the evidence if this may need to be reported.",
        "",
        "## Original Text",
        "",
        "```txt",
        input_text or "(No text provided)",
        "```",
    ])

    return "\n".join(lines)
