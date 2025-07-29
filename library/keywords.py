from selenium.webdriver.common.by import By
from collections import Counter
from collections import defaultdict

def find_all_interactable(driver):
    selectors = [
        "button",
        "input",
        "select",
        "textarea",
        "a[href]",
        "[role='button']",
        "[role='link']",
        "[role='checkbox']",
        "[role='menuitem']",
        "[role='tab']",
        "[role='switch']",
        "[role='slider']",
        "[role='textbox']",
        "[contenteditable='true']",
        "[tabindex]:not([tabindex='-1'])"
    ]
    elements = []
    for sel in selectors:
        elements.extend(driver.find_elements(By.CSS_SELECTOR, sel))

    seen = set()
    unique_elements = []
    for e in elements:
        if e._id in seen:
            continue
        try:
            text = e.text.strip()
            value = e.get_attribute("value") or ""
            placeholder = e.get_attribute("placeholder") or ""
            if text or value.strip() or placeholder.strip() or e.get_attribute("contenteditable") == "true":
                unique_elements.append(e)
                seen.add(e._id)
        except Exception:
            continue
    return unique_elements

def find_all_non_interactable(driver):
    """
    Finds non-interactable elements by subtracting from all visible DOM elements.
    Filters out script, style, and head/meta tags.

    Returns:
        list: List of WebElements that are non-interactable but still rendered.
    """
    interactables = set(find_all_interactable(driver))
    all_elements = driver.find_elements(By.CSS_SELECTOR, "*")

    excluded_tags = {"script", "style", "meta", "head", "link", "title"}
    unique_non_interactables = []
    seen_signatures = set()

    for el in all_elements:
        try:
            if el in interactables:
                continue

            tag = el.tag_name.lower()
            if tag in excluded_tags:
                continue

            signature = driver.execute_script("return arguments[0].outerHTML;", el)
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_non_interactables.append(el)
        except Exception:
            continue

    return unique_non_interactables

def highlight_all(driver, elements=None):
    """
    Highlights elements with outlines and adds numbered badges showing their tag names.
    Different colors are used for different tag types.
    """
    if elements is None:
        elements = find_all_interactable(driver)

    color_map = {
        "button": "dodgerblue",
        "input": "green",
        "select": "orange",
        "a": "purple",
        "div": "gray",
        "default": "red"
    }

    for index, elem in enumerate(elements, 1):
        try:
            tag = elem.tag_name.lower()
            color = color_map.get(tag, color_map["default"])

            script = f"""
            const elem = arguments[0];
            const rect = elem.getBoundingClientRect();

            // Outline the element
            elem.style.outline = '3px solid {color}';
            elem.style.position = 'relative';

            // Create a badge if not already created
            let badge = document.createElement('div');
            badge.textContent = '#{index}: {tag}';
            badge.style.position = 'absolute';
            badge.style.top = '-10px';
            badge.style.left = '-10px';
            badge.style.backgroundColor = '{color}';
            badge.style.color = 'white';
            badge.style.fontSize = '10px';
            badge.style.padding = '2px 4px';
            badge.style.borderRadius = '4px';
            badge.style.zIndex = '9999';
            badge.style.pointerEvents = 'none';
            badge.className = 'selenium-highlight-badge';

            elem.appendChild(badge);
            """

            driver.execute_script(script, elem)
        except Exception:
            continue

def group_elements_by_tag(elements):
    """
    Groups elements by their tag name and visibility.
    
    Returns:
        dict: {tag: {"visible": [...], "hidden": [...]}}
    """
    grouped = defaultdict(lambda: {"visible": [], "hidden": []})
    for el in elements:
        try:
            tag = el.tag_name.lower()
            if el.is_displayed():
                grouped[tag]["visible"].append(el)
            else:
                grouped[tag]["hidden"].append(el)
        except Exception:
            continue
    return grouped

def print_all_elements_info(elements):
    """
    Print relevant information for a list of elements,
    skipping blank or unhelpful fields like 'No Name', etc.
    """
    for i, el in enumerate(elements, 1):
        tag = el.tag_name
        info = {
            "Name": el.get_attribute("name"),
            "Type": el.get_attribute("type"),
            "Placeholder": el.get_attribute("placeholder"),
            "Value": el.get_attribute("value"),
            "Text": el.text.strip(),
            "ID": el.get_attribute("id"),
        }

        # Clean out unhelpful entries
        cleaned_info = {
            key: val for key, val in info.items()
            if val and not val.strip().lower().startswith("no") and val.strip() != ""
        }

        # Format printout
        print(f"\n#{i}: <{tag}>")
        for key, val in cleaned_info.items():
            print(f"  {key}: {val}")


##################################################
            #   Function Calls 
##################################################


def print_all_non_interactable_info(driver):
    """
    Finds and prints grouped summary and details for non-interactable elements.
    """
    elements = find_all_non_interactable(driver)
    grouped = group_elements_by_tag(elements)

    print("\n📋 NON-INTERACTABLE ELEMENTS INFO:")

    total_visible = total_hidden = 0
    detailed_elements = []

    for tag, groups in grouped.items():
        vis_count = len(groups["visible"])
        hid_count = len(groups["hidden"])
        total_visible += vis_count
        total_hidden += hid_count
        print(f"<{tag}>: {vis_count} visible, {hid_count} hidden")
        detailed_elements.extend(groups["visible"])  # You can change to include hidden too

    print(f"\n✅ Total visible non-interactable elements: {total_visible}")
    print(f"🚫 Total hidden non-interactable elements: {total_hidden}\n")

def highlight_and_print(driver):
    """
    Finds all interactable elements, groups them by tag and visibility,
    highlights visible ones, and prints a summary + detailed info.
    """
    all_elements = find_all_interactable(driver)
    grouped = group_elements_by_tag(all_elements)

    # Highlight visible elements only
    visible_elements = [el for group in grouped.values() for el in group["visible"]]
    highlight_all(driver, visible_elements)

    print("\n📋 DETAILED INFO FOR VISIBLE ELEMENTS:")
    print_all_elements_info(visible_elements)

    print("🔍 ELEMENT SUMMARY BY TAG:\n")
    total_visible = total_hidden = 0

    for tag, groups in grouped.items():
        vis_count = len(groups["visible"])
        hid_count = len(groups["hidden"])
        total_visible += vis_count
        total_hidden += hid_count
        print(f"<{tag}>: {vis_count} visible, {hid_count} hidden")

    print(f"\n✅ Total visible elements: {total_visible}")
    print(f"🚫 Total hidden elements: {total_hidden}\n")

def print_dom_tree(driver, root=None):
    """
    Recursively prints a high-level DOM tree starting from root element.
    
    Args:
        driver: Selenium WebDriver instance.
        root: WebElement to start from (defaults to <html> if None).
        max_depth: Maximum depth to recurse into DOM.
        level: Current recursion depth (used internally).
    """
    if root is None:
        root = driver.find_element(By.TAG_NAME, "html")
    
    indent = "  " * level
    try:
        tag = root.tag_name
        el_id = root.get_attribute("id")
        el_class = root.get_attribute("class")
        
        # Format attributes if present
        attrs = []
        if el_id:
            attrs.append(f"id='{el_id}'")
        if el_class:
            attrs.append(f"class='{el_class}'")
        attr_str = " " + " ".join(attrs) if attrs else ""
        
        print(f"{indent}<{tag}{attr_str}>")
        
        
        
        if len(root.find_elements(By.XPATH, "./*")) > 0:
                print(f"{indent}  ...")
        return
        
        # Recurse on children
        children = root.find_elements(By.XPATH, "./*")
        for child in children:
            print_dom_tree(driver, child, max_depth, level + 1)
    except Exception as e:
        print(f"{indent}[Error accessing element: {e}]")

def count_all_tags(driver):
    """
    Counts all tag names in the DOM.

    Args:
        driver: Selenium WebDriver instance.

    Returns:
        dict: Mapping of tag_name -> count
    """
    all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
    tag_counts = Counter()

    for el in all_elements:
        try:
            tag = el.tag_name.lower()
            tag_counts[tag] += 1
        except Exception:
            continue

    return dict(tag_counts)

def automation_ai_insight(tag_counts):
    """
    Generates an AI-style insight about which tags are important for automation
    and testing based on the tags found in the DOM.
    """
    total_tags = sum(tag_counts.values())
    unique_tags = len(tag_counts)

    # Core interactable elements - primary focus for automation and testing
    primary_interactable_tags = {"button", "input", "select", "textarea", "a", "option", "label"}
    # Secondary interactables - good to test, esp for accessibility and toggle elements
    secondary_interactable_tags = {"checkbox", "radio", "switch", "slider", "tab", "menuitem"}

    present_primary = primary_interactable_tags.intersection(tag_counts.keys())
    present_secondary = secondary_interactable_tags.intersection(tag_counts.keys())

    primary_count = sum(tag_counts.get(tag, 0) for tag in present_primary)
    secondary_count = sum(tag_counts.get(tag, 0) for tag in present_secondary)

    structural_tags = {"div", "span", "form", "section", "article", "header", "footer", "nav"}
    present_structural = structural_tags.intersection(tag_counts.keys())

    response_lines = [
        "AI Automation Insight:",
        "----------------------",
        f"This page contains {total_tags} total elements across {unique_tags} unique tag types.\n",
        "Priority 1 - Automate & Test (Core Interactable Elements):",
    ]

    if present_primary:
        for tag in sorted(present_primary):
            response_lines.append(f"  - <{tag}>: {tag_counts[tag]} elements")
    else:
        response_lines.append("  - No core interactable elements detected.")

    if present_secondary:
        response_lines.append("\nPriority 2 - Test Accessibility & Toggles (Secondary Interactable Elements):")
        for tag in sorted(present_secondary):
            response_lines.append(f"  - <{tag}>: {tag_counts[tag]} elements")

    response_lines.append("\nAdditional Notes:")
    response_lines.append(
        f"  - Approximately {primary_count} core interactable elements should be the main targets for simulating user interactions."
    )
    response_lines.append(
        f"  - Around {secondary_count} secondary elements like checkboxes and sliders should be tested for accessibility and toggling behavior."
    )

    if present_structural:
        response_lines.append(
            f"  - Structural elements such as {', '.join(f'<{tag}>' for tag in sorted(present_structural))} "
            "structure the page layout and may require testing if they contain dynamic content or behaviors."
        )
    else:
        response_lines.append("  - No major structural elements detected or needing special automation focus.")

    response_lines.append(
        "\nRecommendation: Focus automation efforts on core interactable elements to cover the main user workflows, "
        "while also including tests for accessibility features and any dynamic structural components."
    )

    return "\n".join(response_lines)

def main(driver):
    print("🔎 Counting all tags on the page...")
    tag_counts = count_all_tags(driver)
    for tag, count in sorted(tag_counts.items()):
        print(f"<{tag}>: {count}")
    print()
    print(automation_ai_insight(tag_counts))
    print("\n" + "="*50 + "\n")

    print("🔎 Highlighting and printing interactable elements...")
    highlight_and_print(driver)
    print("\n" + "="*50 + "\n")

    print("🔎 Printing non-interactable elements summary...")
    print_all_non_interactable_info(driver)
    print("\n" + "="*50 + "\n")
    
main(driver)