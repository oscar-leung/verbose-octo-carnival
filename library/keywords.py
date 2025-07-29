from selenium.webdriver.common.by import By

def find_all_interactable(driver):
    """
    Find all interactable elements: buttons, inputs, selects, links, and role=button elements.
    Filters out elements with no visible text, value, or placeholder.
    Returns a list of WebElements without duplicates.
    """
    selectors = [
        "button",
        "input",
        "select",
        "a[href]",
        "[role='button']"
    ]
    elements = []
    for sel in selectors:
        found = driver.find_elements(By.CSS_SELECTOR, sel)
        elements.extend(found)

    # Filter and remove duplicates
    seen = set()
    unique_elements = []
    for e in elements:
        if e._id in seen:
            continue
        try:
            text = e.text.strip()
            value = e.get_attribute("value") or ""
            placeholder = e.get_attribute("placeholder") or ""
            if text or value.strip() or placeholder.strip():
                unique_elements.append(e)
                seen.add(e._id)
        except Exception:
            continue
    return unique_elements

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




def highlight_and_print(driver):
    """
    Convenience function to find, highlight, and print info for all interactable elements.
    """
    elements = find_all_interactable(driver)
    highlight_all(driver, elements)
    print_all_elements_info(elements)
