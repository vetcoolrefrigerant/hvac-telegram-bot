import math

def calculate_heating_load(data):
    # Simple heating load
    q_walls = data['u_walls'] * data['area_walls'] * (data['t_indoor'] - data['t_outdoor'])
    q_windows = data['u_windows'] * data['area_windows'] * (data['t_indoor'] - data['t_outdoor'])
    q_roof = data['u_roof'] * data['area_roof'] * (data['t_indoor'] - data['t_outdoor'])
    q_conduction = q_walls + q_windows + q_roof

    cfm = (data['volume'] * data['ach']) / 60
    q_infil = 1.08 * cfm * (data['t_indoor'] - data['t_outdoor'])

    total = q_conduction + q_infil
    return {
        'total_btu_hr': round(total),
        'cfm': round(cfm, 1)
    }


def calculate_cooling_load(data):
    # Simple cooling load
    q_walls = data['u_walls'] * data['area_walls'] * 25
    q_roof = data['u_roof'] * data['area_roof'] * 40
    q_windows = data['u_windows'] * data['area_windows'] * 12
    q_solar = data['area_windows'] * 140   # simplified

    cfm = (data['volume'] * data.get('ach', 0.5)) / 60
    q_inf_s = 1.08 * cfm * (data['t_outdoor'] - data['t_indoor'])
    q_inf_l = 0.68 * cfm * 30

    q_people = data.get('occupants', 0) * 380
    q_lights = data.get('lighting_watts', 0) * 3.41

    sensible = q_walls + q_roof + q_windows + q_solar + q_inf_s + q_people + q_lights
    latent = q_inf_l
    total = sensible + latent

    return {
        'total_btu_hr': round(total),
        'tons': round(total / 12000, 2),
        'cfm': round(sensible / (1.08 * 20))
    }