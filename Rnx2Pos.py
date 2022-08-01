class Rnx2Pos:
    match_list = dict()
    pos_paths = dict()

    def read_dir():
        pass

    def read_list(self, input_rover: list, input_base=[], input_nav=[], input_sp3_clk=[], input_sbas_ionex_fcb=[]) -> dict:
        if not isinstance(input_rover, (list, tuple)):
            return print("Error. The 'input_rover' variable must be of type 'list' or 'tuple'.")
        elif not isinstance(input_base, (list, tuple)):
            return print("Error. The 'input_base' variable must be of type 'list' or 'tuple'.")
        elif not isinstance(input_nav, (list, tuple)):
            return print("Error. The 'input_nav' variable must be of type 'list' or 'tuple'.")
        elif not isinstance(input_sp3_clk, (list, tuple)):
            return print("Error. The 'input_sp3_clk' variable must be of type 'list' or 'tuple'.")
        elif not isinstance(input_sbas_ionex_fcb, (list, tuple)):
            return print("Error. The 'input_sbas_ionex_fcb' variable must be of type 'list' or 'tuple'.")
        
        return 

    def start():
        pass


if __name__ == "__main__":
    pass
