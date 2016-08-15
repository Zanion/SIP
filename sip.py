# !/usr/bin/env python
# -*- coding: utf-8 -*-

import i18n

import json
import ast
import time
import thread
from calendar import timegm
import sys
sys.path.append('./plugins')

import web  # the Web.py module. See webpy.org (Enables the Python SIP web interface)

import gv
from helpers import plugin_adjustment, prog_match, schedule_stations, log_run, stop_onrain, check_rain, jsave, station_names, get_rpi_revision
from urls import urls  # Provides access to URLs for UI pages
from gpio_pins import set_output
from ReverseProxied import ReverseProxied

# do not call set output until plugins are loaded because it should NOT be called
# if gv.use_gpio_pins is False (which is set in relay board plugin.
# set_output()


def OneMinuteHasElapsed(last_min):
    """
    Return if a full minute has elapsed since the last minute
    """
    SECONDS_PER_MINUTE = 60
    return gv.CurrentTime() / SECONDS_PER_MINUTE != last_min


def GetStationIndex(board_offset, station_offset):
    """
    Return the index of the station provided the index of the board and the index of
    the station on the board.
    """
    STATIONS_PER_BOARD = 8
    return board_offset * STATIONS_PER_BOARD + station_offset


def timing_loop():
    """ ***** Main timing algorithm. Runs in a separate thread.***** """
    try:
        print _('Starting timing loop') + '\n'
    except Exception:
        pass
    last_min = 0
    while True:  # infinite loop
        gv.nowt = time.localtime()   # Current time as time struct.  Updated once per second.
        gv.now = timegm(gv.nowt)   # Current time as timestamp based on local time from the Pi. Updated once per second.
        if gv.IsEnabled() and gv.IsAutoMode() and (gv.IsIdle() or gv.IsConcurrent()):
            if OneMinuteHasElapsed(last_min):  # only check programs once a minute
                last_min = gv.CurrentTime() / 60
                extra_adjustment = plugin_adjustment()
                for index, program in enumerate(gv.ProgramData()):  # get both index and prog item
                    # check if program time matches current time, is active, and has a duration
                    if prog_match(program) and program[0] and program[6]:
                        # check each station for boards listed in program up to number of boards in Options
                        for board in range(len(program[7:7 + gv.NumberOfBoards()])):
                            for station in range(8):
                                sid = GetStationIndex(board, station)
                                if gv.StationIsMaster(sid):
                                    continue  # skip if this is master station
                                if gv.srvals[sid]:  # skip if currently on
                                    continue

                                # station duration conditionally scaled by "water level"
                                if gv.sd['iw'][board] & 1 << station:
                                    duration_adj = 1.0
                                    duration = program[6]
                                else:
                                    duration_adj = gv.WaterLevelDurationAdjustment(extra_adjustment)
                                    duration = program[6] * duration_adj
                                    duration = int(round(duration)) # convert to int
                                if program[7 + board] & 1 << station:  # if this station is scheduled in this program
                                    # Skip if concurrent and duration is shorter than existing station duration
                                    if gv.IsConcurrent() and duration < gv.rs[sid][2]:
                                        continue
                                    gv.rs[sid][2] = duration
                                    gv.rs[sid][3] = index + 1  # store program number for scheduling
                                    gv.ps[sid][0] = index + 1  # store program number for display
                                    gv.ps[sid][1] = duration
                        schedule_stations(program[7:7 + gv.NumberOfBoards()])  # turns on gv.sd['bsy']

        if gv.IsBusy():
            for b in range(gv.NumberOfBoards()):  # Check each station once a second
                for s in range(8):
                    sid = b * 8 + s  # station index
                    if gv.srvals[sid]:  # if this station is on
                        if gv.StationPassedScheduledStopTime(sid):  # check if time is up
                            gv.srvals[sid] = 0
                            set_output()
                            gv.sbits[b] &= ~(1 << s)
                            if not gv.StationIsMaster(sid):  # if not master, fill out log
                                gv.ClearUIProgramScheduleForStation(sid)
                                gv.lrun[0] = sid
                                gv.lrun[1] = gv.rs[sid][3]
                                gv.lrun[2] = int(gv.CurrentTime() - gv.rs[sid][0])
                                gv.lrun[3] = gv.CurrentTime()
                                log_run()
                                gv.pon = None  # Program has ended
                            gv.rs[sid] = [0, 0, 0, 0]
                    else:  # if this station is not yet on
                        if gv.rs[sid][0] <= gv.CurrentTime() < gv.rs[sid][1]:
                            if not gv.StationIsMaster(sid):
                                gv.srvals[sid] = 1  # station is turned on
                                set_output()
                                gv.sbits[b] |= 1 << s  # Set display to on
                                gv.ps[sid][0] = gv.rs[sid][3]
                                gv.ps[sid][1] = gv.rs[sid][2]
                                if gv.MasterStationAssigned() and gv.sd['mo'][b] & 1 << (s - (s / 8) * 80):  # Master settings
                                    masid = gv.IndexOfMasterStation()  # master index
                                    gv.rs[masid][0] = gv.rs[sid][0] + gv.MasterOnDelay()
                                    gv.rs[masid][1] = gv.rs[sid][1] + gv.MasterOffDelay()
                                    gv.rs[masid][3] = gv.rs[sid][3]
                            else:
                                gv.sbits[b] |= 1 << sid  # (gv.sd['mas'] - 1)
                                gv.srvals[masid] = 1
                                set_output()

            program_running = gv.IsProgramRunning()

            if program_running:
                if gv.IsRainSensorUsed() and gv.IsRainSensed():  # Stop stations if use rain sensor and rain detected.
                    stop_onrain()  # Clear schedule for stations that do not ignore rain.
                for idx in range(len(gv.rs)):  # loop through program schedule (gv.ps)
                    if gv.rs[idx][2] == 0:  # skip stations with no duration
                        continue
                    if gv.srvals[idx]:  # If station is on, decrement time remaining display
                        gv.ps[idx][1] -= 1

            if not program_running:
                gv.srvals = [0] * (gv.NumberOfStations())
                set_output()
                gv.sbits = [0] * (gv.NumberOfBoards() + 1)
                gv.ClearUIProgramScheduleForAllStations()
                gv.rs = []
                for i in range(gv.NumberOfStations()):
                    gv.rs.append([0, 0, 0, 0])
                gv.SetIdle()

            if gv.MasterStationAssigned() and (gv.IsManualMode() or gv.IsConcurrent()):  # handle master for manual or concurrent mode.
                mval = 0
                for sid in range(gv.NumberOfStations()):
                    bid = sid / 8
                    s = sid - bid * 8
                    if not gv.StationIsMaster(sid) and (gv.srvals[sid] and gv.sd['mo'][bid] & 1 << s):
                        mval = 1
                        break
                if not mval:
                    gv.rs[gv.IndexOfMasterStation()][1] = gv.CurrentTime()  # turn off master

        check_rain()  # in helpers.py

        if gv.RainDelayStopTimeExpired():  # Check of rain delay time is up
            gv.SetRainDelayInHours(0)
            gv.SetRainDelayStopTime(0)
            jsave(gv.sd, 'sd')
        time.sleep(1)
        #### End of timing loop ####


class SIPApp(web.application):
    """Allow program to select HTTP port."""

    def run(self, port=gv.sd['htp'], *middleware):  # get port number from options settings
        func = self.wsgifunc(*middleware)
        func = ReverseProxied(func)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))


app = SIPApp(urls, globals())
#  disableShiftRegisterOutput()
web.config.debug = False  # Improves page load speed
if web.config.get('_session') is None:
    web.config._session = web.session.Session(app, web.session.DiskStore('sessions'),
                                              initializer={'user': 'anonymous'})
template_globals = {
    'gv': gv,
    'str': str,
    'eval': eval,
    'session': web.config._session,
    'json': json,
    'ast': ast,
    '_': _,
    'i18n': i18n,
    'app_path': lambda p: web.ctx.homepath + p,
    'web' : web,
}

template_render = web.template.render('templates', globals=template_globals, base='base')

if __name__ == '__main__':

    #########################################################
    #### Code to import all webpages and plugin webpages ####

    import plugins

    try:
        print _('plugins loaded:')
    except Exception:
        pass
    for name in plugins.__all__:
        print ' ', name

    gv.plugin_menu.sort(key=lambda entry: entry[0])

    # Ensure first three characters ('/' plus two characters of base name of each
    # plugin is unique.  This allows the gv.plugin_data dictionary to be indexed
    # by the two characters in the base name.
    plugin_map = {}
    for p in gv.plugin_menu:
        three_char = p[1][0:3]
        if three_char not in plugin_map:
            plugin_map[three_char] = p[0] + '; ' + p[1]
        else:
            print 'ERROR - Plugin Conflict:', p[0] + '; ' + p[1] + ' and ', plugin_map[three_char]
            exit()

    #  Keep plugin manager at top of menu
    try:
        gv.plugin_menu.pop(gv.plugin_menu.index(['Manage Plugins', '/plugins']))
    except Exception:
        pass

    thread.start_new_thread(timing_loop, ())

    if gv.use_gpio_pins:
        set_output()


    app.notfound = lambda: web.seeother('/')

    app.run()
