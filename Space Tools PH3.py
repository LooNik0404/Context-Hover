import maya.cmds as cmds
import maya.mel as mel
import math

# Формулы для режимов Easy In и Easy Out
def logarithmic_ease_in(t):
    t = max(0.0001, min(t, 1.0))  # Ограничиваем t в пределах (0, 1]
    return 1 - (math.log10(1 + 9 * (1 - t)))

def logarithmic_ease_out(t):
    t = max(0.0001, min(t, 1.0))  # Ограничиваем t в пределах (0, 1]
    return math.log10(t * 9 + 1)

# Упрощенные формулы для режимов Centre Easy In и Centre Easy Out
def centre_ease_in_left(t):
    return logarithmic_ease_in(t)

def centre_ease_in_right(t):
    return logarithmic_ease_out(t)

def centre_ease_out_left(t):
    return logarithmic_ease_out(t)

def centre_ease_out_right(t):
    return logarithmic_ease_in(t)

def get_selected_channelbox_attributes():
    return cmds.channelBox('mainChannelBox', query=True, selectedMainAttributes=True) or []

def store_time_slider_selection():
    gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
    time_slider_range = cmds.timeControl(gPlayBackSlider, q=True, rangeArray=True)
    current_time = cmds.currentTime(query=True)
    return time_slider_range, current_time

def restore_time_slider_selection(time_slider_range, current_time):
    gPlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
    cmds.timeControl(gPlayBackSlider, e=True, rangeArray=time_slider_range)
    cmds.currentTime(current_time, edit=True)

def get_available_attributes(obj):
    attrs = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']
    available_attrs = [attr for attr in attrs if cmds.attributeQuery(attr, node=obj, exists=True)]
    return available_attrs

def store_original_key_data(selected_objects, selected_attributes):
    original_key_data = {}
    attributes = set()
    for obj in selected_objects:
        obj_attrs = ["{}.{}".format(obj, attr) for attr in selected_attributes] if selected_attributes else get_available_attributes(obj)
        for attr in obj_attrs:
            key_times = cmds.keyframe(attr, query=True, timeChange=True)
            key_values = cmds.keyframe(attr, query=True, valueChange=True)
            if key_times and key_values:
                original_key_data[attr] = {t: v for t, v in zip(key_times, key_values)}
                attributes.add(attr)
    return original_key_data, list(attributes)

def calculate_eased_times(original_times, start_time, end_time, ease_type):
    total_duration = end_time - start_time
    mid_time = start_time + total_duration / 2
    new_times = []

    for t in original_times:
        relative_time = (t - start_time) / total_duration
        if ease_type == 'Easy In':
            eased_time = logarithmic_ease_in(relative_time)
            new_time = start_time + eased_time * total_duration
        elif ease_type == 'Easy Out':
            eased_time = logarithmic_ease_out(relative_time)
            new_time = start_time + eased_time * total_duration
        elif ease_type == 'Centre Easy In':
            if t < mid_time:
                eased_time = centre_ease_in_left((t - start_time) / (mid_time - start_time))
                new_time = start_time + eased_time * (mid_time - start_time)
            else:
                eased_time = centre_ease_in_right((t - mid_time) / (end_time - mid_time))
                new_time = mid_time + eased_time * (end_time - mid_time)
        elif ease_type == 'Centre Easy Out':
            if t < mid_time:
                eased_time = centre_ease_out_left((t - start_time) / (mid_time - start_time))
                new_time = start_time + eased_time * (mid_time - start_time)
            else:
                eased_time = centre_ease_out_right((t - mid_time) / (end_time - mid_time))
                new_time = mid_time + eased_time * (end_time - mid_time)
        new_times.append(new_time)

    return new_times

def apply_blend(ease_type, blend_value):
    time_slider_range, current_time = store_time_slider_selection()
    selected_objects = cmds.ls(selection=True)

    if not selected_objects:
        cmds.warning("Пожалуйста, выберите объект.")
        return

    start_time, end_time = time_slider_range
    if end_time <= start_time:
        cmds.warning("Некорректный временной диапазон.")
        return

    selected_attributes = get_selected_channelbox_attributes()
    if not selected_attributes:
        selected_attributes = get_available_attributes(selected_objects[0])
    original_key_data, attributes = store_original_key_data(selected_objects, selected_attributes)

    # Включаем ускорение анимации
    cmds.evaluationManager(mode="off")

    for attr in attributes:
        if attr not in original_key_data:
            continue
        original_times = sorted([t for t in original_key_data[attr].keys() if start_time <= t <= end_time])
        if not original_times:
            continue
        eased_times = calculate_eased_times(original_times, start_time, end_time, ease_type)
        new_times = [(1 - blend_value) * orig_time + blend_value * eased_time for orig_time, eased_time in zip(original_times, eased_times)]

        keyframes = []
        for old_time, new_time in zip(original_times, new_times):
            value = original_key_data[attr][old_time]
            keyframes.append((new_time, value))
            if old_time != new_time:
                cmds.cutKey(attr, time=(old_time,))

        for new_time, value in keyframes:
            cmds.setKeyframe(attr, time=new_time, value=value)

    # Возвращаемся к нормальному режиму
    cmds.evaluationManager(mode="parallel")

    restore_time_slider_selection(time_slider_range, current_time)

def update_blend_value_display(*args):
    blend_value = cmds.floatSlider(blend_slider, query=True, value=True)
    cmds.text(blend_value_display, edit=True, label="Blend Value: {:.2f}".format(blend_value))

def update_blend(*args):
    update_blend_value_display()

def apply_blend_button(*args):
    blend_value = cmds.floatSlider(blend_slider, query=True, value=True)
    ease_type = cmds.optionMenu(ease_type_menu, query=True, value=True)
    apply_blend(ease_type, blend_value)

def open_ease_window():
    if cmds.window("easeWindow", exists=True):
        cmds.deleteUI("easeWindow")

    cmds.window("easeWindow", title="Ease Settings", widthHeight=(300, 250))
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label="Select the easing type:", align="center")
    global ease_type_menu
    ease_type_menu = cmds.optionMenu()
    cmds.menuItem(label="Easy In")
    cmds.menuItem(label="Easy Out")
    cmds.menuItem(label="Centre Easy In")
    cmds.menuItem(label="Centre Easy Out")

    cmds.separator(height=20)
    cmds.text(label="Blend to Original", align="center")
    global blend_slider
    blend_slider = cmds.floatSlider(min=0.0, max=1.0, value=0.0, step=0.01, changeCommand=update_blend)

    global blend_value_display
    blend_value_display = cmds.text(label="Blend Value: 0.00", align="center")

    cmds.separator(height=20)
    cmds.button(label="Apply", command=apply_blend_button)

    cmds.showWindow("easeWindow")

# Открыть окно для настройки силы easing
open_ease_window()
