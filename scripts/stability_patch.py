from pathlib import Path
p=Path('backend/waypoint/navigation.py');s=p.read_text();s=s.replace('        self.ba+=correction[9:12]; self.bg+=correction[12:15]', '        self.ba=np.clip(self.ba+correction[9:12],-2.,2.); self.bg=np.clip(self.bg+correction[12:15],-.1,.1)')
s=s.replace('    def gps(self, xy, velocity, noise):','    def planar(self):\n        if self.filtered:\n            H=np.zeros((2,15));H[0,2]=1;H[1,5]=1\n            self.update(np.array([-self.p[2],-self.v[2]]),H,.5)\n\n    def gps(self, xy, velocity, noise):')
s=s.replace('            self.p[:2]=xy','            self.p[:2]=xy;self.p[2]=0;self.v[2]=0')
s=s.replace("            for f in filters.values(): f.gps(ref[i],measured_velocity,config.get('gps_noise',5))", "            for f in filters.values():\n                f.gps(ref[i],measured_velocity,config.get('gps_noise',5))\n                if measured_velocity is not None and np.linalg.norm(measured_velocity)>2:\n                    forward=f.r.apply([0,1,0]); observed=np.arctan2(measured_velocity[0],measured_velocity[1]); estimated=np.arctan2(forward[0],forward[1]); difference=(estimated-observed+np.pi)%(2*np.pi)-np.pi\n                    f.r=Rotation.from_rotvec([0,0,difference*.1])*f.r")
s=s.replace('        for name,f in filters.items():\n            paths', '        for f in filters.values(): f.planar()\n        for name,f in filters.items():\n            paths')
s=s.replace("'engine_version':'1.0.0'", "'engine_version':'1.0.1'")
s=s.replace("'GPS reference accuracy limits the measured errors.'", "'GPS reference accuracy limits the measured errors.','Ground-vehicle planar constraints and bounded sensor-bias priors are applied. Available GPS course stabilizes yaw above 2 m/s.'")
p.write_text(s)
