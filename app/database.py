from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///app/main.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)

role_map = {
    "TOP": ["TOP"],
    "JGL": ["JGL", "JUNGLE", "JUNG", "JNG", "JG"],
    "MID": ["MID", "MIDDLE"],
    "ADC": ["ADC", "CARRY", "BOT", "BOTLANE"],
    "SUP": ["SUP", "SUPPORT", "SUPP"]
}

def standardize_role(role):
    for standard_role, variations in role_map.items():
        if role.upper() in variations:
            return standard_role
    return None



class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True)
    discord_id = Column(String, nullable=False)
    ign = Column(String, nullable=False)
    region = Column(String, nullable=False, default="NA") # NA, EUW, EUN
    rating = Column(Integer, nullable=False, default=1500)
    deviation = Column(Integer, nullable=False, default=350)
    role1 = Column(String, nullable=False, default="MID")
    role2 = Column(String, nullable=False, default="TOP")
    in_game = Column(Integer, nullable=False, default=0) # 0 false 1 true

    def __repr__(self):
        return f'<Player(discord_id={self.discord_id}, ign={self.ign}, role={self.role1}, rating={self.rating})>'


class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    winner = Column(Integer, default=0) #0 in progress, 1 team1, 2 team2
    # Team 1
    player_1_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player_2_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player_3_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player_4_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player_5_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    # Team 2
    player_6_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player_7_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player_8_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player_9_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player_10_id = Column(Integer, ForeignKey('players.id'), nullable=False)

    def __repr__(self):
        return f'<Match(id={self.id})>'


if __name__ == "__main__":
    pass
    print("creating all for the DB")
    Base.metadata.create_all(engine)