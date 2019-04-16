from multiprocessing import Process
from irvedge import irv_edge


def simulate(n):
    for i in range(n):
        name = f"irv-edge-{i}"
        subprocess = Process(target=irv_edge, args=(name,))
        subprocess.start()


if __name__ == "__main__":
    n = 10
    simulate(n)

