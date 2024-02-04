from io import StringIO


def export_model_to_txt(suffix, model):
    """Exports the model to a text file"""
    stream = StringIO()
    model.pprint(ostream=stream)
    with open("model_" + suffix + ".txt", "w") as f:
        f.write(stream.getvalue())
