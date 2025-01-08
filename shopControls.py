import discord

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view

        # Dynamically add buttons for all cards in the shop
        for card in shop:
            self.add_item(discord.ui.Button(
                label=f"Buy {card['card_name']} - {card['cost']} coins",
                style=discord.ButtonStyle.green,
                custom_id=f"buy_{card['card_number']}"
            ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Callback for all buttons
        custom_id = interaction.data['custom_id']  # Get the button's custom_id
        for card in shop:
            if custom_id == f"buy_{card['card_number']}":
                await interaction.response.send_message(
                    f"You purchased **{card['card_name']}** for {card['cost']} coins!",
                    ephemeral=True
                )
                return True
        return False