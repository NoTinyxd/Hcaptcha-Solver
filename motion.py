import numpy as np
import scipy.interpolate
import string
import random
import math
import time


class util:
    @staticmethod
    def randint(a, b):
        return random.randint(min(a, b), max(a, b))

    @staticmethod
    def get_ms():
        return int(time.time() * 1000)

    @staticmethod
    def distance(a, b):
        return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

    @staticmethod
    def periods(timestamps):
        p = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        return sum(p) / len(p) if p else 0

    @staticmethod
    def get_random_point(bbox):
        x1, y1 = int(bbox[0][0]), int(bbox[0][1])
        x2, y2 = int(bbox[1][0]), int(bbox[1][1])
        return util.randint(x1, x2), util.randint(y1, y2)

    @staticmethod
    def get_center(bbox):
        x1, y1 = int(bbox[0][0]), int(bbox[0][1])
        x2, y2 = int(bbox[1][0]), int(bbox[1][1])
        return int(x1 + (x2 - x1) / 2), int(y1 + (y2 - y1) / 2)

    @staticmethod
    def get_windmouse(start, goal, screen_size, max_points, gravity=9, wind=3, min_wait=1, max_wait=3, max_step=15, target_area=10):
        start = (int(start[0]), int(start[1]))
        goal = (int(goal[0]), int(goal[1]))
        screen_size = (int(screen_size[0]), int(screen_size[1]))
        current = list(start)
        points = [[current[0], current[1], util.get_ms()]]

        while util.distance(current, goal) > 1:
            gv = [goal[0] - current[0], goal[1] - current[1]]
            gm = math.sqrt(gv[0] ** 2 + gv[1] ** 2)
            if gm > 0:
                gv = [gv[0] / gm * gravity, gv[1] / gm * gravity]
            wa = random.uniform(0, 2 * math.pi)
            wv = [math.cos(wa) * wind, math.sin(wa) * wind]
            force = [gv[0] + wv[0], gv[1] + wv[1]]
            fm = math.sqrt(force[0] ** 2 + force[1] ** 2)
            if fm > max_step:
                force = [force[0] / fm * max_step, force[1] / fm * max_step]
            current = [current[0] + force[0], current[1] + force[1]]
            if util.distance(current, goal) < target_area:
                j = random.uniform(-1, 1)
                current[0] += j
                current[1] += j
            current[0] = max(0, min(screen_size[0], current[0]))
            current[1] = max(0, min(screen_size[1], current[1]))
            points.append([int(current[0]), int(current[1]), util.get_ms()])
            if len(points) >= max_points:
                break

        points[-1] = [goal[0], goal[1], points[-1][2]]
        return points

    @staticmethod
    def get_bezier_spline(start, goal, screen_size, max_points):
        mid_x = (start[0] + goal[0]) / 2 + random.randint(-abs(goal[0]-start[0])//3, abs(goal[0]-start[0])//3)
        mid_y = (start[1] + goal[1]) / 2 + random.randint(-abs(goal[1]-start[1])//3, abs(goal[1]-start[1])//3)
        mid_x = max(0, min(screen_size[0], mid_x))
        mid_y = max(0, min(screen_size[1], mid_y))
        points = np.array([
            [start[0], start[1]],
            [mid_x, mid_y],
            [goal[0], goal[1]]
        ])
        t = np.linspace(0, 1, len(points))
        t_new = np.linspace(0, 1, max_points)
        try:
            cs_x = scipy.interpolate.CubicSpline(t, points[:, 0])
            cs_y = scipy.interpolate.CubicSpline(t, points[:, 1])
            x_new = cs_x(t_new)
            y_new = cs_y(t_new)
        except Exception:
            x_new = np.linspace(start[0], goal[0], max_points)
            y_new = np.linspace(start[1], goal[1], max_points)
        return list(zip(x_new.astype(int), y_new.astype(int)))

    @staticmethod
    def get_mm(start, goal, screen_size, max_points, random_amount, polling_rate):
        points = util.get_windmouse(start, goal, screen_size, max_points)

        if random.random() > 0.5 and len(points) > 3:
            curve_points = util.get_bezier_spline(start, goal, screen_size, min(len(points), max_points))
            for i, (x, y) in enumerate(curve_points):
                if i < len(points):
                    points[i] = [int(x), int(y), points[i][2]]

        timestamps = [p[2] for p in points]
        for i, (x, y, t) in enumerate(points):
            x += random.randint(-random_amount // 2, random_amount // 2)
            y += random.randint(-random_amount // 2, random_amount // 2)
            x = max(0, min(screen_size[0], x))
            y = max(0, min(screen_size[1], y))
            if i > 0:
                delta = random.randint(polling_rate // 2, polling_rate * 2)
                t = timestamps[i - 1] + delta
            points[i] = [x, y, t]

        return points


class rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_dimensions(self):
        return self.width, self.height

    def get_box(self, rel_x, rel_y):
        rel_x, rel_y = int(rel_x), int(rel_y)
        return (rel_x, rel_y), (rel_x + self.width, rel_y + self.height)

    def get_corners(self, rel_x=0, rel_y=0):
        rel_x, rel_y = int(rel_x), int(rel_y)
        return [
            (rel_x, rel_y),
            (rel_x + self.width, rel_y),
            (rel_x, rel_y + self.height),
            (rel_x + self.width, rel_y + self.height)
        ]


class widget_check:
    def __init__(self, rel_position):
        self.widget = rectangle(300, 75)
        self.check_box = rectangle(28, 28)
        self.rel_position = rel_position

    def get_check(self):
        return self.check_box.get_box(16 + self.rel_position[0], 23 + self.rel_position[1])

    def get_closest(self, position):
        corners = self.widget.get_corners(self.rel_position[0], self.rel_position[1])
        sorted_corners = sorted(corners, key=lambda c: util.distance(position, c))
        return sorted_corners[0], sorted_corners[1]


COMMON_SCREEN_SIZES = [
    (1024, 768), (1280, 720), (1280, 800), (1280, 960), (1280, 1024),
    (1366, 768), (1440, 900), (1600, 900), (1600, 1200), (1680, 1050),
    (1920, 1080), (1920, 1200), (2048, 1152), (2560, 1440), (2560, 1600),
    (3440, 1440), (3840, 2160), (3840, 1600)
]
COMMON_CORE_COUNTS = [2, 4, 6, 8, 10, 12, 16, 24, 32, 64]


class get_cap:
    def __init__(self, user_agent, href):
        self.user_agent = user_agent
        self.screen_size = random.choice(COMMON_SCREEN_SIZES)
        widget_id = '0' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        random_point = util.get_random_point(((0, 0), (self.screen_size[0] - 150, self.screen_size[1] - 38)))
        self.widget = widget_check(random_point)
        self.position = util.get_random_point(((0, 0), self.screen_size))

        self.data = {
            'st': util.get_ms(),
            'mm': [],
            'mm-mp': 0,
            'md': [],
            'md-mp': 0,
            'mu': [],
            'mu-mp': 0,
            'v': 1,
            'topLevel': self._top_level(),
            'session': [],
            'widgetList': [widget_id],
            'widgetId': widget_id,
            'href': href,
            'prev': {
                'escaped': False,
                'passed': False,
                'expiredChallenge': False,
                'expiredResponse': False
            }
        }

        goal = util.get_random_point(self.widget.get_check())
        mm = util.get_mm(self.position, goal, self.screen_size, 30, 5, 8)
        self.data['mm'] = [[x - random_point[0], y - random_point[1], t] for x, y, t in mm]
        self.data['mm-mp'] = util.periods([p[2] for p in mm])

        n_clicks = random.randint(1, 3)
        md_events = []
        mu_events = []
        for _ in range(n_clicks):
            base = self.data['mm'][-1]
            jx = base[0] + random.randint(-2, 2)
            jy = base[1] + random.randint(-2, 2)
            md_t = util.get_ms()
            md_events.append([jx, jy, md_t])
            mu_events.append([jx, jy, md_t + random.randint(80, 180)])

        self.data['md'] = md_events
        self.data['mu'] = mu_events
        self.data['md-mp'] = util.periods([e[2] for e in md_events]) if len(md_events) > 1 else 0
        self.data['mu-mp'] = util.periods([e[2] for e in mu_events]) if len(mu_events) > 1 else 0

    def _top_level(self):
        sw, sh = self.screen_size
        st = util.get_ms()

        position = tuple(int(v) for v in self.position)
        goal = util.get_random_point(self.widget.get_closest(position))
        mm = util.get_mm(position, goal, self.screen_size, 60, 4, 12)
        self.position = tuple(int(v) for v in goal)

        mm_lists = [[x, y, t] for x, y, t in mm]
        mm_mp = util.periods([p[2] for p in mm_lists])

        wn_t = util.get_ms()
        wn_events = [[sw, sh, 1, wn_t]]
        wn_mp = 0

        xy_t = util.get_ms()
        xy_events = [[0, 0, 1, xy_t]]
        xy_mp = 0

        cores = random.choice(COMMON_CORE_COUNTS)
        lang = random.choice(['en-US', 'nl-NL', 'de-DE'])
        touch = random.choice([0, 1, 5])

        return {
            'inv': False,
            'st': st,
            'sc': {
                'availWidth': sw,
                'availHeight': sh,
                'width': sw,
                'height': sh,
                'colorDepth': 24,
                'pixelDepth': 24,
                'top': 0,
                'left': 0,
                'availTop': 0,
                'availLeft': 0,
                'mozOrientation': 'landscape-primary',
                'onmozorientationchange': None
            },
            'nv': {
                'permissions': {},
                'pdfViewerEnabled': True,
                'doNotTrack': 'unspecified',
                'maxTouchPoints': touch,
                'mediaCapabilities': {},
                'vendor': 'Google Inc.',
                'vendorSub': 'Chrome',
                'cookieEnabled': True,
                'mediaDevices': {},
                'serviceWorker': {},
                'credentials': {},
                'clipboard': {},
                'mediaSession': {},
                'webdriver': False,
                'hardwareConcurrency': cores,
                'geolocation': {},
                'userAgent': self.user_agent,
                'language': lang,
                'languages': ['en-US', 'en'],
                'locks': {},
                'onLine': True,
                'storage': {},
                'connection': {},
                'bluetooth': {},
                'usb': {},
                'scheduling': {},
                'wakeLock': {},
                'xr': {},
                'plugins': [
                    'Chrome PDF Plugin',
                    'Chrome PDF Viewer',
                    'Native Client',
                    'Widevine Content Decryption Module'
                ]
            },
            'dr': '',
            'exec': False,
            'wn': wn_events,
            'wn-mp': wn_mp,
            'xy': xy_events,
            'xy-mp': xy_mp,
            'mm': mm_lists,
            'mm-mp': mm_mp
        }


class motion_data:
    def __init__(self, user_agent, url):
        self.user_agent = user_agent
        self.url = url
        self._cap = get_cap(user_agent, url)

    def get_captcha(self):
        return self._cap.data

    def check_captcha(self):
        return get_cap(self.user_agent, self.url).data