from flask import Flask, render_template, request, session, redirect, url_for
from state import Player
from module.ai import AI
from module.db import DB, DBs
from pathlib import Path

app = Flask(__name__)
app.secret_key = "some_secret_key"  # 需要一个秘钥来启用 Flask sessions

# 初始化AI、DB等
ai = AI(
    model_name = "gpt-3.5-turbo-16k",
    temperature = 0.1,
)

input_path = Path("projects/example").absolute()
memory_path = input_path / "memory"
workspace_path = input_path / "workspace"
archive_path = input_path / "archive"
dbs = DBs(
    memory=DB(memory_path),
    logs=DB(memory_path / "logs"),
    input=DB(input_path),
    workspace=DB(workspace_path),
    preprompts=DB(Path(__file__).parent / "prompts"),
    archive=DB(archive_path),
)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 从表单中获取用户的选择
        choice = request.form.get('choice')
        player = Player.from_dict(session['player'])

        # 处理选择
        player.undergo_event(ai, dbs, choice)
        session['player'] = player.to_dict()

        # 检查玩家状态
        status = player.check_status(ai, dbs)
        if status < 0:
            return render_template('game_over.html', player=player)  # 假设有一个game_over模板

        return redirect(url_for('index'))

    # 如果玩家还没初始化，就初始化他
    if 'player' not in session:
        session['player'] = Player().to_dict()  # 假设Player有一个to_dict方法来存储其状态

    player = Player.from_dict(session['player'])  # 假设有一个from_dict方法来从状态中重建玩家

    # 生成事件
    if player.age < 5:
        player.birth_event(ai, dbs)
        render_template('index.html', player=player, event_description=player.experiences[-1])
    
    player.event_gen(ai, dbs)

    return render_template('index.html', player=player, event_description=player.experiences[-1])

if __name__ == '__main__':
    app.run(debug=True)
