import click
import time
from click_prompt import auto_complete_option

noteTypes = ["essay", "report", "video", "note"]

@click.command()
@click.argument("title")
@click.option("--tags", type=str, default="")
@auto_complete_option("--notetype", "-t", type=click.Choice(noteTypes),)
@click.pass_context
def createNewNote(ctx: click.Context, title: str, tags: str, notetype)->None:
    notesDirectory = ctx.obj["notes_directory"]

    content = click.prompt("What would you like the note to say?")
    click.echo(f"Note of type {notetype}")
    if click.confirm("Are you sure you want to save the note?"):
        with open(notesDirectory + "/" + title + ".txt", "w") as noteFile:
            noteFile.write(content)
        
        click.echo(click.style('Creating note', bold=True, blink=True))

        with click.progressbar(length=20) as bar:
            for i in range(20):
                time.sleep(1/20)
                bar.update(1)

        click.echo(click.style('Created note :)', fg='green'))
        return
    click.echo(click.style('Note Canceled', fg='red'))

