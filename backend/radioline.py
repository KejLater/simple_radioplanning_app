

class Radioline:
    """
    Class describes behavior of 
    signal between tx and rx 
    based on distance between tx-rx, 
    rain density, frequency, gains.
    """
    def __init__(self, Ptx: float, Gtx: float, Grx: float, d: float, f: float, rain_density: int|str|None=None):
        """
        Ptx - power of sourse signal [dB]
        Gtx - gain of transmitter [dB]
        Grx - gain of receiver [dB]
        d - distance between tx and rx [km]
        f - signal frequency [GHz]
        rain_density - None/0/5/25/50/100/150/200 [mm per hour] (Optional).
        """

        # TODO validation
        self._Ptx = Ptx
        self._Gtx = Gtx
        self._Grx = Grx
        self._d = d
        self._f = f
        self._rain_density = rain_density

    @property
    def RSSI(self) -> float:
        """
        Calculates RSSI.
        """
        return self._Ptx + self._Gtx - self.FSPL - self.rain_attenuation - self.atmosphere_attenuation + self._Grx


    @property
    def FSPL(self) -> float:
        """
        Calculates Free Space Propagation Loss.
        """
        from math import log10
        return 92.45 + 20*log10(self._d) + 20*log10(self._f)


    @property
    def rain_attenuation(self) -> float:
        """
        Calculates signal attenuation [dB] based
        on rain density, if rain density is 
        0 or None, 0 will be returned.
        """
        if not self._rain_density or self._rain_density == '0':
            return 0
        else:
            import pandas as pd

            schema = {
                'freq_GHz': float,
                'att_dB_per_km': float,
                'rain_rate_mm_per_h': str
            }

            df = pd.read_csv('./data/rain_attenuation.csv', sep=',', decimal='.', dtype=schema)
            df_filtered = df[df.rain_rate_mm_per_h==str(self._rain_density)]
            idx = (df_filtered.freq_GHz - self._f).abs().idxmin()
            return df_filtered.loc[idx, 'att_dB_per_km']


    @property
    def atmosphere_attenuation(self) -> float:
        import pandas as pd

        schema = {
            'freq_GHz': float,
            'att_dB_per_km': float,
        }

        df = pd.read_csv('./data/atmosphere_attenuation.csv', sep=',', decimal='.', dtype=schema)
        idx = (df.freq_GHz - self._f).abs().idxmin()
        return df.loc[idx, 'att_dB_per_km']

line = Radioline(10,10,15,5,14)
print(line.RSSI)