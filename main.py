from watermarker import Config, process

config = Config.load("config.yaml")

if __name__ == "__main__":
    process(config, "input", "output")
